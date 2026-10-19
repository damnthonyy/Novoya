/** An error answered by the API: its HTTP status and the `code` of its ErrorResponse body. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/**
 * Turns the body the generated client throws into an ApiError, with the response's status.
 * A network or CORS failure has no response: its error is kept as it is.
 */
export function toApiError(body: unknown, response: Response | undefined): unknown {
  if (!response) return body
  const { code, detail } = (typeof body === 'object' && body !== null ? body : {}) as {
    code?: unknown
    detail?: unknown
  }
  return new ApiError(
    response.status,
    typeof code === 'string' ? code : 'unknown',
    typeof detail === 'string' ? detail : typeof body === 'string' ? body : response.statusText,
  )
}

/** No session, or it expired or was revoked: the only error that means "go to /login". */
export function isUnauthenticated(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401 && error.code === 'unauthenticated'
}
