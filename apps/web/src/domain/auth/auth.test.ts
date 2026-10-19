import { describe, expect, it } from 'vitest'

import en from '../../i18n/locales/en/errors.json'
import { passwordSignInErrorKey, signInErrorKey } from './errors'
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

  it('accepts up to 512 characters, like the API', () => {
    const longest = '/' + 'a'.repeat(511)
    expect(safeRedirect(longest)).toBe(longest)
    expect(safeRedirect(longest + 'a')).toBe('/')
  })

  it.each([undefined, '', 'https://evil.com', '//evil.com', '/\\evil.com', '/a\nb', 42])(
    'falls back to / for %j',
    (target) => {
      expect(safeRedirect(target)).toBe('/')
    },
  )
})

describe('signInErrorKey', () => {
  it('is null without an error', () => {
    expect(signInErrorKey(undefined)).toBeNull()
  })

  it('gives the key of a known code and a fallback for the others', () => {
    expect(signInErrorKey('account_disabled')).toBe('signIn.account_disabled')
    expect(signInErrorKey('oauth_cancelled')).toBe('signIn.oauth_cancelled')
    expect(signInErrorKey('something_new')).toBe('signIn.unknown')
  })

  it('has a text for every key it can give', () => {
    const codes = Object.keys(en.signIn)
    for (const code of [...codes, 'something_new']) {
      const key = signInErrorKey(code)!.replace('signIn.', '')
      expect(en.signIn).toHaveProperty(key)
    }
  })
})

describe('passwordSignInErrorKey', () => {
  it('gives the key of a known code', () => {
    expect(passwordSignInErrorKey('invalid_credentials')).toBe('password.invalid_credentials')
    expect(passwordSignInErrorKey('email_not_verified')).toBe('password.email_not_verified')
  })

  it('reads a rate limit like too many attempts', () => {
    expect(passwordSignInErrorKey('too_many_requests')).toBe('password.too_many_attempts')
  })

  it('has a fallback for anything else', () => {
    expect(passwordSignInErrorKey(undefined)).toBe('password.unknown')
    expect(passwordSignInErrorKey('something_new')).toBe('password.unknown')
  })

  it('has a text for every key it can give', () => {
    for (const code of [...Object.keys(en.password), 'too_many_requests', 'something_new']) {
      const key = passwordSignInErrorKey(code).replace('password.', '')
      expect(en.password).toHaveProperty(key)
    }
  })
})
