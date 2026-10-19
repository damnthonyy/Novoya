export type Locale = 'en' | 'fr'

/**
 * The language of the interface: the signed-in user's locale (from /me), else the browser's
 * first language, else English. Same rule as the API's Locale.from_hint, which reads the
 * first language of Accept-Language: fr if it starts with "fr", en otherwise.
 */
export function resolveLocale(
  userLocale: Locale | undefined,
  browserLanguages: readonly string[],
): Locale {
  if (userLocale) return userLocale
  return browserLanguages[0]?.trim().toLowerCase().startsWith('fr') ? 'fr' : 'en'
}
