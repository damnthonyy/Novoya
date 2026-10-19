type Destination = { country: string; city: string | null }

// Our partners' destinations have their own photo; anything else gets the neutral sea one.
const BY_CITY: Record<string, string> = {
  chania: '/images/elounda-sea-view.jpg',
  elounda: '/images/elounda-sea-view.jpg',
  biarritz: '/images/biarritz-surf.jpg',
  marrakech: '/images/marrakech-riad.jpg',
}
const BY_COUNTRY: Record<string, string> = {
  greece: '/images/crete-coast.jpg',
  grèce: '/images/crete-coast.jpg',
  france: '/images/biarritz-surf.jpg',
  morocco: '/images/marrakech-riad.jpg',
  maroc: '/images/marrakech-riad.jpg',
}
export const FALLBACK_PHOTO = '/images/aegean-boat.jpg'

const key = (value: string | null) => (value ?? '').trim().toLowerCase()

/** A photo for a destination: its city's, else its country's, else a neutral one. */
export function destinationPhoto(destination: Destination): string {
  return BY_CITY[key(destination.city)] ?? BY_COUNTRY[key(destination.country)] ?? FALLBACK_PHOTO
}

/** "Chania · Greece", or the country alone. */
export function destinationLabel(destination: Destination): string {
  return destination.city ? `${destination.city} · ${destination.country}` : destination.country
}

/** The place to name in a wish started from a suggestion: the city, else the country. */
export function destinationPlace(destination: Destination): string {
  return destination.city ?? destination.country
}
