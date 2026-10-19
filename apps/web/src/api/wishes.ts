import type { WishResponse } from './generated/types.gen'

/** A wish answered by POST /wishes, with the text the client wrote (the response does not repeat it). */
export type CachedWish = WishResponse & { text: string }

/**
 * Where the wish answered by POST /wishes is kept for the preferences page.
 * There is no GET /wishes/{id} yet, so after a reload the page cannot find it again.
 */
export const wishQueryKey = (wishId: string) => ['wish', wishId] as const

export type { WishResponse }
