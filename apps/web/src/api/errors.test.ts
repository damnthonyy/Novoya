import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import './client'
import { ApiError, isUnauthenticated } from './errors'
import { getMe } from './generated/sdk.gen'
import { client } from './generated/client.gen'

describe('isUnauthenticated', () => {
  it('is true only for a 401 with the unauthenticated code', () => {
    expect(isUnauthenticated(new ApiError(401, 'unauthenticated', 'not signed in'))).toBe(true)
    expect(isUnauthenticated(new ApiError(401, 'invalid_credentials', 'wrong password'))).toBe(false)
    expect(isUnauthenticated(new ApiError(500, 'unauthenticated', 'odd'))).toBe(false)
    expect(isUnauthenticated({ code: 'unauthenticated' })).toBe(false)
    expect(isUnauthenticated(new TypeError('Failed to fetch'))).toBe(false)
  })
})

describe('the API client', () => {
  beforeEach(() => client.setConfig({ baseUrl: 'http://api.test' }))
  afterEach(() => vi.restoreAllMocks())

  it('throws an ApiError with the status and code of the answer', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      Response.json({ code: 'unauthenticated', detail: 'not signed in' }, { status: 401 }),
    )

    const error = await getMe({ throwOnError: true }).catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 401, code: 'unauthenticated', message: 'not signed in' })
  })

  it('keeps a body that is not JSON', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('Bad gateway', { status: 502 }))

    const error = await getMe({ throwOnError: true }).catch((e: unknown) => e)

    expect(error).toMatchObject({ status: 502, code: 'unknown', message: 'Bad gateway' })
  })

  it('keeps a network error as it is', async () => {
    const failure = new TypeError('Failed to fetch')
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(failure)

    await expect(getMe({ throwOnError: true })).rejects.toBe(failure)
  })
})
