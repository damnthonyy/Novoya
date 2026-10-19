import 'i18next'

import type auth from './locales/en/auth.json'
import type common from './locales/en/common.json'
import type errors from './locales/en/errors.json'
import type header from './locales/en/header.json'
import type home from './locales/en/home.json'
import type wish from './locales/en/wish.json'

// The English files are the reference: t() only accepts keys that exist in them.
// Add each new namespace (screen) here.
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common'
    resources: {
      auth: typeof auth
      common: typeof common
      errors: typeof errors
      header: typeof header
      home: typeof home
      wish: typeof wish
    }
  }
}
