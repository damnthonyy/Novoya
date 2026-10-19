import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'

import { isUnauthenticated } from '../api/errors'
import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'
import { resolveLocale } from '../domain/i18n/locale'
import i18n from '../i18n'

// Every page under this layout needs a session. Without one, go to /login and come back after.
// Any other failure (API down, network, 500) is rethrown so the error page shows it.
export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ context, location }) => {
    try {
      const me = await context.queryClient.ensureQueryData({ ...getMeOptions(), retry: false })
      // Switch before the page renders, so it never shows in the browser's language first.
      const locale = resolveLocale(me.locale, navigator.languages)
      if (i18n.language !== locale) await i18n.changeLanguage(locale)
      return { me }
    } catch (error) {
      if (isUnauthenticated(error)) {
        throw redirect({ to: '/login', search: { redirect: location.href } })
      }
      throw error
    }
  },
  component: Outlet,
})
