/** The name to show for the signed-in user. Google accounts may have none, so fall back to the email. */
export function displayName(user: { name: string | null; email: string }): string {
  return user.name?.trim() || user.email
}

// oxlint-disable-next-line no-control-regex -- rejecting control characters is the point
const CONTROL = /[\x00-\x1f\x7f]/
const MAX_LENGTH = 512 // RedirectPolicy.max_length and the oauth_states.redirect_to column

/**
 * A page of the web app to go to after signing in, or `fallback`.
 * Same rule as the API's RedirectPolicy: a relative path, never another site.
 */
export function safeRedirect(target: unknown, fallback = '/'): string {
  if (typeof target !== 'string' || !target || target.length > MAX_LENGTH) return fallback
  if (!target.startsWith('/') || target.startsWith('//') || target.startsWith('/\\')) return fallback
  if (CONTROL.test(target)) return fallback
  return target
}
