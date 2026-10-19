// The codes the API puts in /login?error=<code> when a Google sign-in fails.
const MESSAGES: Record<string, string> = {
  oauth_cancelled: 'You cancelled the Google sign-in.',
  oauth_failed: 'Google sign-in did not work. Please try again.',
  oauth_state_invalid: 'Your sign-in took too long or was started in another browser. Please try again.',
  oauth_email_not_verified: 'Your Google email address is not verified yet.',
  oauth_link_not_allowed: 'This Google account cannot be linked to your Novoya account.',
  identity_already_linked: 'This Google account is already linked to another Novoya account.',
  account_disabled: 'This account is disabled.',
  user_not_found: 'We could not find your account. Please sign in again.',
  too_many_attempts: 'Too many attempts. Please wait a moment and try again.',
  unknown_provider: 'Sign-in with Google is not available right now.',
}

const FALLBACK = 'Something went wrong while signing you in. Please try again.'

/** The message to show for a sign-in error code, or null when there is no error. */
export function signInErrorMessage(code: string | undefined): string | null {
  if (!code) return null
  return MESSAGES[code] ?? FALLBACK
}
