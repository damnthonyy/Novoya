import type { QueryClient } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { createRootRouteWithContext, Outlet, useRouter } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

import { ErrorNote } from '../components/molecules/ErrorNote'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootLayout,
})

// Public pages (landing, login) draw their own header; signed-in pages get theirs from /_authenticated.
function RootLayout() {
  return (
    <>
      <Outlet />
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
  return (
    <main className="pt-24">
      <ErrorNote
        message="Novoya ne parvient pas à joindre le serveur. Réessayez dans un instant."
        onRetry={() => router.invalidate()}
      />
    </main>
  )
}
