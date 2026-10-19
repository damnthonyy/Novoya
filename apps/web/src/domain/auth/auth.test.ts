import { describe, expect, it } from 'vitest'

import { signInErrorMessage } from './errors'
import { displayName, safeRedirect } from './session'

describe('displayName', () => {
  it('uses the name', () => {
    expect(displayName({ name: 'Léa Martin', email: 'lea@example.com' })).toBe('Léa Martin')
  })

  it('falls back to the email when there is no name', () => {
    expect(displayName({ name: null, email: 'lea@example.com' })).toBe('lea@example.com')
    expect(displayName({ name: '  ', email: 'lea@example.com' })).toBe('lea@example.com')
  })
})

describe('safeRedirect', () => {
  it('keeps a page of the app', () => {
    expect(safeRedirect('/wishes/new?x=1')).toBe('/wishes/new?x=1')
  })

  it.each([undefined, '', 'https://evil.com', '//evil.com', '/\\evil.com', '/a\nb', 42])(
    'falls back to / for %j',
    (target) => {
      expect(safeRedirect(target)).toBe('/')
    },
  )
})

describe('signInErrorMessage', () => {
  it('is null without an error', () => {
    expect(signInErrorMessage(undefined)).toBeNull()
  })

  it('explains a known code and has a fallback for the others', () => {
    expect(signInErrorMessage('account_disabled')).toBe('This account is disabled.')
    expect(signInErrorMessage('something_new')).toMatch(/went wrong/)
  })
})
