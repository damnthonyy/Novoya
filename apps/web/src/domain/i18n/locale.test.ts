import { describe, expect, it } from 'vitest'

import { resolveLocale } from './locale'

describe('resolveLocale', () => {
  it("uses the signed-in user's locale first", () => {
    expect(resolveLocale('fr', ['en-US'])).toBe('fr')
    expect(resolveLocale('en', ['fr-FR'])).toBe('en')
  })

  it("falls back to the browser's first language", () => {
    expect(resolveLocale(undefined, ['fr-CA', 'en'])).toBe('fr')
    expect(resolveLocale(undefined, ['FR'])).toBe('fr')
  })

  it('only looks at the first language, like the API', () => {
    expect(resolveLocale(undefined, ['en-GB', 'fr-FR'])).toBe('en')
  })

  it('is English for any other language, or none', () => {
    expect(resolveLocale(undefined, ['de-DE'])).toBe('en')
    expect(resolveLocale(undefined, [])).toBe('en')
  })
})
