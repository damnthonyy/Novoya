import { createFileRoute, redirect } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { googleSignInUrl } from '../api/auth'
import { isUnauthenticated } from '../api/errors'
import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'
import { ButtonLink } from '../components/atoms/Button'
import { signInErrorKey } from '../domain/auth/errors'
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
    throw redirect({ href: safeRedirect(search.redirect) })
  },
  component: LoginPage,
})

function LoginPage() {
  const { redirect: target, error } = Route.useSearch()
  const { t } = useTranslation('auth')
  const { t: tErrors } = useTranslation('errors')
  const errorKey = signInErrorKey(error)

  return (
    <section className="login">
      <h1>{t('title')}</h1>
      <p>{t('intro')}</p>
      {errorKey && (
        <p role="alert" className="login__error">
          {tErrors(errorKey)}
        </p>
      )}
      <ButtonLink href={googleSignInUrl(safeRedirect(target))}>{t('continueWithGoogle')}</ButtonLink>
    </section>
  )
}
