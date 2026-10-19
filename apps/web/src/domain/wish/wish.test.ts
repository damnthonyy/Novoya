import { describe, expect, it } from 'vitest'

import { destinationLabel, destinationPhoto, FALLBACK_PHOTO, suggestionWish } from './destination'
import { sendWishErrorMessage, WISH_MAX_LENGTH, wishTextError } from './wish'

describe('wishTextError', () => {
  it('accepts a sentence', () => {
    expect(wishTextError('Une semaine calme au bord de la mer')).toBeNull()
  })

  it('refuses an empty or blank wish', () => {
    expect(wishTextError('')).toMatch(/Décrivez votre envie/)
    expect(wishTextError('   \n ')).toMatch(/Décrivez votre envie/)
  })

  it('refuses more than the API takes, ignoring the spaces around', () => {
    expect(wishTextError(` ${'a'.repeat(WISH_MAX_LENGTH)} `)).toBeNull()
    expect(wishTextError('a'.repeat(WISH_MAX_LENGTH + 1))).toMatch(/1000 caractères/)
  })
})

describe('sendWishErrorMessage', () => {
  it('explains a refused wish and rate limiting, with a fallback', () => {
    expect(sendWishErrorMessage('invalid_wish')).toMatch(/Reformulez/)
    expect(sendWishErrorMessage('too_many_requests')).toMatch(/Patientez/)
    expect(sendWishErrorMessage(undefined)).toMatch(/n’a pas pu être envoyée/)
  })
})

describe('destinationPhoto', () => {
  it('uses the city first, then the country, ignoring case', () => {
    expect(destinationPhoto({ city: 'Chania', country: 'Greece' })).toBe('/images/elounda-sea-view.jpg')
    expect(destinationPhoto({ city: 'Athens', country: 'greece' })).toBe('/images/crete-coast.jpg')
    expect(destinationPhoto({ city: null, country: 'Morocco' })).toBe('/images/marrakech-riad.jpg')
  })

  it('falls back to a neutral photo', () => {
    expect(destinationPhoto({ city: 'Kyoto', country: 'Japan' })).toBe(FALLBACK_PHOTO)
  })
})

describe('destinationLabel and suggestionWish', () => {
  it('name the city when there is one', () => {
    expect(destinationLabel({ city: 'Biarritz', country: 'France' })).toBe('Biarritz · France')
    expect(destinationLabel({ city: null, country: 'France' })).toBe('France')
    expect(suggestionWish({ city: 'Biarritz', country: 'France' })).toBe('Quelques jours à Biarritz, ')
    expect(suggestionWish({ city: null, country: 'Maroc' })).toBe('Quelques jours à Maroc, ')
  })
})
