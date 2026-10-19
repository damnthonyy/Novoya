import { createFileRoute, redirect } from '@tanstack/react-router'

import { googleSignInUrl } from '../api/auth'
import { isUnauthenticated } from '../api/errors'
import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'
import { Button } from '../components/atoms/Button'
import { signInErrorMessage } from '../domain/auth/errors'
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
  const message = signInErrorMessage(error)

  return (
    <main className="mx-auto max-w-md px-5 pt-24">
      <h1 className="mb-3 text-5xl">Se connecter</h1>
      <p className="mb-6 text-muted">Retrouvez vos envies, vos aperçus et toutes vos conversations.</p>
      {message && (
        <p role="alert" className="mb-4 text-danger">
          {message}
        </p>
      )}
      <Button asChild variant="outline" className="w-full">
        <a href={googleSignInUrl(safeRedirect(target, '/wish'))}>Continuer avec Google</a>
      </Button>
    </main>
  )
}
