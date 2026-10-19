/** The API's limit for a wish's text (SendWishRequest). */
export const WISH_MAX_LENGTH = 1000

/** Why the wish cannot be sent yet, or null when it can. */
export function wishTextError(text: string): string | null {
  const trimmed = text.trim()
  if (!trimmed) return 'Décrivez votre envie en quelques mots.'
  if (trimmed.length > WISH_MAX_LENGTH) {
    return `Votre envie est un peu longue : ${WISH_MAX_LENGTH} caractères au plus.`
  }
  return null
}

/** The API's codes for a refused wish, in words for the client. */
export function sendWishErrorMessage(code: string | undefined): string {
  if (code === 'invalid_wish') return 'Nous n’avons pas pu lire cette envie. Reformulez-la en une phrase.'
  if (code === 'too_many_requests' || code === 'too_many_attempts') return 'Trop de demandes d’un coup. Patientez un instant puis réessayez.'
  return 'Votre envie n’a pas pu être envoyée. Réessayez dans un instant.'
}
