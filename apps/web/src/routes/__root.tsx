import { type QueryClient, useMutation, useQueryClient } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import {
  createRootRouteWithContext,
  Outlet,
  useRouter,
  useRouterState,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { getMeQueryKey, signOutMutation } from '../api/generated/@tanstack/react-query.gen'
import { ErrorNote } from '../components/molecules/ErrorNote'
import { AppHeader } from '../components/organisms/AppHeader'
import { displayName } from '../domain/auth/session'
import { resolveLocale } from '../domain/i18n/locale'
import { useActivityGap } from '../hooks/ui/useActivityGap'
import i18n from '../i18n'

// After this long without any action on the page, check the session again on the next navigation.
const IDLE_MS = 3 * 60_000

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootLayout,
})

function RootLayout() {
  const queryClient = useQueryClient()
  const router = useRouter()
  // The user loaded by the /_authenticated guard. Pages outside it, like /login, have none.
  const me = useRouterState({
    select: (state) => state.matches.find((match) => match.routeId === '/_authenticated')?.context.me,
  })
  const signOut = useMutation({
    ...signOutMutation(),
    onSuccess: async () => {
      queryClient.clear()
      await router.navigate({ to: '/login' })
    },
    // On failure the session cookie may still be valid: stay here and say so.
  })

  const { t } = useTranslation('header')

  useActivityGap(IDLE_MS, () => queryClient.removeQueries({ queryKey: getMeQueryKey() }))

  // The signed-in user's locale wins; signed out (e.g. on /login), the browser's language.
  // The /_authenticated guard already switches before a signed-in page renders; this keeps
  // the language right when there is no user any more, for example after signing out.
  const locale = resolveLocale(me?.locale, navigator.languages)
  useEffect(() => {
    if (i18n.language !== locale) void i18n.changeLanguage(locale)
  }, [locale])

  return (
    <>
      <AppHeader
        userName={me ? displayName(me) : undefined}
        onSignOut={() => signOut.mutate({})}
        signingOut={signOut.isPending}
        signOutError={signOut.isError ? t('signOutFailed') : undefined}
      />
      <main className="app-main">
        <Outlet />
      </main>
      {import.meta.env.DEV && (
        <>
          <TanStackRouterDevtools position="bottom-right" />
          <ReactQueryDevtools buttonPosition="bottom-left" />
        </>
      )}
    </>
  )
}

/** The page shown when a route fails for another reason than a missing session. */
export function RouteError() {
  const router = useRouter()
  const { t } = useTranslation('errors')
  return (
    <ErrorNote
      message={t('serverUnreachable')}
      onRetry={() => router.invalidate()}
    />
  )
}
