// The codes the API puts in /login?error=<code> when a Google sign-in fails.
// Their texts are in i18n/locales/<language>/errors.json, under signIn.<code>.
const SIGN_IN_ERROR_CODES = [
  'oauth_cancelled',
  'oauth_failed',
  'oauth_state_invalid',
  'oauth_email_not_verified',
  'oauth_link_not_allowed',
  'identity_already_linked',
  'account_disabled',
  'user_not_found',
  'too_many_attempts',
  'unknown_provider',
] as const

type SignInErrorCode = (typeof SIGN_IN_ERROR_CODES)[number]
export type SignInErrorKey = `signIn.${SignInErrorCode | 'unknown'}`

const KNOWN = new Set<string>(SIGN_IN_ERROR_CODES)

/** The key of the message to show for a sign-in error code, or null when there is no error. */
export function signInErrorKey(code: string | undefined): SignInErrorKey | null {
  if (!code) return null
  return KNOWN.has(code) ? (`signIn.${code}` as SignInErrorKey) : 'signIn.unknown'
}
