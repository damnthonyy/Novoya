import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'

import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'

// Every page under this layout needs a session. Without one, go to /login and come back after.
export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ context, location }) => {
    try {
      const me = await context.queryClient.ensureQueryData({ ...getMeOptions(), retry: false })
      return { me }
    } catch {
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
  },
  component: Outlet,
})
