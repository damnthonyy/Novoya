import type { QueryClient } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import {
  createRootRouteWithContext,
  Link,
  Outlet,
  useRouter,
  useRouterState,
} from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

import { Logo } from '../components/atoms/Logo'
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
  // Inside the signed-in layout, its header is already on screen. Otherwise (the session
  // check itself failed, or a public page) draw one, so there is still a way home.
  const layoutHeader = useRouterState({
    select: (state) =>
      state.matches.some((match) => match.routeId === '/_authenticated' && match.status === 'success'),
  })
  return (
    <>
      {!layoutHeader && (
        <header className="flex h-18 items-center border-b border-line px-5 md:h-22 md:px-[5vw]">
          <Link to="/" aria-label="Novoya, accueil" className="flex min-h-11 items-center no-underline">
            <Logo />
          </Link>
        </header>
      )}
      <main className={layoutHeader ? 'pt-26 md:pt-30' : 'pt-8'}>
        <ErrorNote
          message="Novoya ne parvient pas à joindre le serveur. Réessayez dans un instant."
          onRetry={() => router.invalidate()}
        />
      </main>
    </>
  )
}
