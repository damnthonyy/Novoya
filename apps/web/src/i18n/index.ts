import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { resolveLocale } from '../domain/i18n/locale'

// One file per language and screen: locales/<language>/<screen>.json (see docs/I18N.md).
// They are all bundled, so a page never shows before its texts. A new file is picked up here
// without any change; declare its namespace in i18next.d.ts for the types.
const files = import.meta.glob<Record<string, unknown>>('./locales/*/*.json', {
  eager: true,
  import: 'default',
}) // every locales/<lang>/<screen>.json, including new screens

export const resources: Record<string, Record<string, Record<string, unknown>>> = {}
for (const [path, messages] of Object.entries(files)) {
  const [, language, namespace] = path.match(/^\.\/locales\/([^/]+)\/([^/]+)\.json$/)!
  ;(resources[language] ??= {})[namespace] = messages
}

export const namespaces = Object.keys(resources.en).sort()

// Keep <html lang> in step, for screen readers and the browser's own features.
i18n.on('languageChanged', (language) => document.documentElement.setAttribute('lang', language))

// Until /me answers, the browser's language decides; routes/__root.tsx switches to the user's.
void i18n.use(initReactI18next).init({
  resources,
  ns: namespaces,
  defaultNS: 'common',
  lng: resolveLocale(undefined, navigator.languages),
  fallbackLng: 'en',
  supportedLngs: ['en', 'fr'],
  interpolation: { escapeValue: false }, // React escapes already
  initAsync: false, // the resources are bundled: ready before the first render
  react: { useSuspense: false },
})

export default i18n
