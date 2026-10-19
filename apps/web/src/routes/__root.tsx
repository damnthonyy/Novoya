import { type QueryClient, useMutation, useQueryClient } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import {
  createRootRouteWithContext,
  Outlet,
  useRouter,
  useRouterState,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

import { signOutMutation } from '../api/generated/@tanstack/react-query.gen'
import { AppHeader } from '../components/organisms/AppHeader'
import { displayName } from '../domain/auth/session'

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
    // Leave the protected pages even if the request failed: nothing of this account stays in memory.
    onSettled: async () => {
      queryClient.clear()
      await router.navigate({ to: '/login' })
    },
  })

  return (
    <>
      <AppHeader
        userName={me ? displayName(me) : undefined}
        onSignOut={() => signOut.mutate({})}
        signingOut={signOut.isPending}
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
