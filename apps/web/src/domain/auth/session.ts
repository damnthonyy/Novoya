/** The name to show for the signed-in user. Google accounts may have none, so fall back to the email. */
export function displayName(user: { name: string | null; email: string }): string {
  return user.name?.trim() || user.email
}

// oxlint-disable-next-line no-control-regex -- rejecting control characters is the point
const CONTROL = /[\x00-\x1f\x7f]/
const MAX_LENGTH = 2048

/**
 * A page of the web app to go to after signing in, or `/`.
 * Same rule as the API's RedirectPolicy: a relative path, never another site.
 */
export function safeRedirect(target: unknown): string {
  if (typeof target !== 'string' || !target || target.length > MAX_LENGTH) return '/'
  if (!target.startsWith('/') || target.startsWith('//') || target.startsWith('/\\')) return '/'
  if (CONTROL.test(target)) return '/'
  return target
}
