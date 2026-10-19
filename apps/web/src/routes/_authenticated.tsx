import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Outlet, redirect, useRouter } from '@tanstack/react-router'

import { isUnauthenticated } from '../api/errors'
import { getMeOptions, getMeQueryKey, signOutMutation } from '../api/generated/@tanstack/react-query.gen'
import { AppHeader } from '../components/organisms/AppHeader'
import { displayName } from '../domain/auth/session'
import { useActivityGap } from '../hooks/ui/useActivityGap'

// After this long without any action on the page, check the session again on the next navigation.
const IDLE_MS = 3 * 60_000

// Every page under this layout needs a session. Without one, go to /login and come back after.
// Any other failure (API down, network, 500) is rethrown so the error page shows it.
export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ context, location }) => {
    try {
      const me = await context.queryClient.ensureQueryData({ ...getMeOptions(), retry: false })
      return { me }
    } catch (error) {
      if (isUnauthenticated(error)) {
        throw redirect({ to: '/login', search: { redirect: location.href } })
      }
      throw error
    }
  },
  component: SignedInLayout,
})

function SignedInLayout() {
  const { me } = Route.useRouteContext()
  const queryClient = useQueryClient()
  const router = useRouter()
  const signOut = useMutation({
    ...signOutMutation(),
    onSuccess: async () => {
      queryClient.clear()
      await router.navigate({ to: '/login' })
    },
    // On failure the session cookie may still be valid: stay here and say so.
  })

  useActivityGap(IDLE_MS, () => queryClient.removeQueries({ queryKey: getMeQueryKey() }))

  return (
    <>
      <AppHeader
        userName={displayName(me)}
        role={me.role}
        onSignOut={() => signOut.mutate({})}
        signingOut={signOut.isPending}
        signOutError={signOut.isError ? 'La déconnexion a échoué. Réessayez.' : undefined}
      />
      <Outlet />
    </>
  )
}
