import 'i18next'

import type admin from './locales/en/admin.json'
import type agent from './locales/en/agent.json'
import type auth from './locales/en/auth.json'
import type common from './locales/en/common.json'
import type concierge from './locales/en/concierge.json'
import type errors from './locales/en/errors.json'
import type header from './locales/en/header.json'
import type home from './locales/en/home.json'
import type plan from './locales/en/plan.json'
import type quote from './locales/en/quote.json'
import type trips from './locales/en/trips.json'
import type wish from './locales/en/wish.json'

// The English files are the reference: t() only accepts keys that exist in them.
// Add each new namespace (screen) here.
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common'
    resources: {
      admin: typeof admin
      agent: typeof agent
      auth: typeof auth
      common: typeof common
      concierge: typeof concierge
      errors: typeof errors
      header: typeof header
      home: typeof home
      plan: typeof plan
      quote: typeof quote
      trips: typeof trips
      wish: typeof wish
    }
  }
}
