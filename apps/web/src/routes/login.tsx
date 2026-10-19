import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link, redirect, useRouter } from '@tanstack/react-router'

import { googleSignInUrl } from '../api/auth'
import { ApiError, isUnauthenticated } from '../api/errors'
import {
  getMeOptions,
  getMeQueryKey,
  signInWithPasswordMutation,
} from '../api/generated/@tanstack/react-query.gen'
import { Button } from '../components/atoms/Button'
import { Eyebrow } from '../components/atoms/Eyebrow'
import { Logo } from '../components/atoms/Logo'
import { AuthMedia } from '../components/organisms/AuthMedia'
import { PasswordSignInForm } from '../components/organisms/PasswordSignInForm'
import { passwordSignInErrorMessage, signInErrorMessage } from '../domain/auth/errors'
import { safeRedirect } from '../domain/auth/session'

type LoginSearch = {
  /** The page to go back to after signing in. */
  redirect?: string
  /** Set by the API when a Google sign-in fails. */
  error?: string
}

export const Route = createFileRoute('/login')({
  validateSearch: (search: Record<string, unknown>): LoginSearch => ({
    redirect: typeof search.redirect === 'string' ? search.redirect : undefined,
    error: typeof search.error === 'string' ? search.error : undefined,
  }),
  // Show the page only when there is no session. Already signed in: go to the requested page.
  // Any other failure is rethrown, so an API outage does not look like being signed out.
  beforeLoad: async ({ context, search }) => {
    try {
      await context.queryClient.ensureQueryData({ ...getMeOptions(), retry: false })
    } catch (error) {
      if (isUnauthenticated(error)) return
      throw error
    }
    throw redirect({ href: safeRedirect(search.redirect, '/wish') })
  },
  component: LoginPage,
})

function LoginPage() {
  const { redirect: target, error } = Route.useSearch()
  const googleError = signInErrorMessage(error)
  const next = safeRedirect(target, '/wish')
  const queryClient = useQueryClient()
  const router = useRouter()
  const signIn = useMutation({
    ...signInWithPasswordMutation(),
    onSuccess: async () => {
      // The 401 from before is stale: the next page asks /me again with the new session cookie.
      queryClient.removeQueries({ queryKey: getMeQueryKey() })
      await router.navigate({ href: next })
    },
  })
  const passwordError = signIn.isError
    ? passwordSignInErrorMessage(signIn.error instanceof ApiError ? signIn.error.code : undefined)
    : undefined

  return (
    <main className="min-h-screen md:grid md:h-screen md:grid-cols-[1.05fr_0.95fr]">
      <AuthMedia
        image="/images/aegean-boat.jpg"
        imageAlt="Bateau sur la mer Égée"
        logo={
          <Link to="/" aria-label="Novoya, accueil" className="flex min-h-11 items-center no-underline">
            <Logo light />
          </Link>
        }
        quote="“On ne devrait pas passer des semaines à chercher un voyage qui nous ressemble.”"
        caption="Mer Égée · Grèce"
      />
      <section className="grid place-items-center bg-paper px-[22px] py-[45px] md:overflow-y-auto md:p-[30px]">
        <div className="w-full max-w-[420px]">
          <Eyebrow>Heureux de vous revoir</Eyebrow>
          <h1 className="mb-2.5 text-[45px] leading-none md:text-[55px]">Se connecter</h1>
          <p className="text-muted">Retrouvez vos envies, vos aperçus et toutes vos conversations.</p>
          {googleError && (
            <p role="alert" className="mt-4 text-sm text-danger">
              {googleError}
            </p>
          )}
          <Button asChild variant="outline" className="my-5 w-full">
            <a href={googleSignInUrl(next)}>
              <span aria-hidden="true" className="font-[Arial] font-bold">
                G
              </span>
              Continuer avec Google
            </a>
          </Button>
          <div className="mb-1 flex items-center gap-2.5 text-xs text-muted">
            <span aria-hidden="true" className="h-px flex-1 bg-line" />
            ou avec votre e-mail
            <span aria-hidden="true" className="h-px flex-1 bg-line" />
          </div>
          <PasswordSignInForm
            onSubmit={(body) => signIn.mutate({ body })}
            pending={signIn.isPending}
            error={passwordError}
          />
          <p className="mt-6 text-center text-xs text-muted">
            En continuant, vous acceptez nos conditions et notre politique de confidentialité.
          </p>
        </div>
      </section>
    </main>
  )
}
