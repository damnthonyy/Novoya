// Demo data until the API exists (issue #51, agent queue).

export type QuoteRequest = {
  id: string
  client: string
  title: string
  wish: string
  /** Whole euros. */
  budget: number
  startDate: string
  endDate: string
  travellers: number
  receivedHoursAgo: number
}

const REQUESTS: QuoteRequest[] = [
  { id: 'r1', client: 'Camille Martin', title: 'Chania, au rythme de la mer', wish: 'Une semaine calme, de bonnes tables et beaucoup de mer.', budget: 3500, startDate: '2026-05-12', endDate: '2026-05-19', travellers: 2, receivedHoursAgo: 1 },
  { id: 'r2', client: 'Nora Bernard', title: 'Marrakech, derrière les portes', wish: 'Un riad au calme, la médina à pied.', budget: 2200, startDate: '2026-06-03', endDate: '2026-06-07', travellers: 2, receivedHoursAgo: 2 },
  { id: 'r3', client: 'Louis Perrin', title: 'Biarritz, plein ouest', wish: 'Du surf le matin, l’océan le soir.', budget: 1800, startDate: '2026-06-18', endDate: '2026-06-21', travellers: 1, receivedHoursAgo: 3 },
]

export type QueueFilter = 'unassigned' | 'in_progress' | 'decided'

/** The quote requests in one tab of the queue. Replace with the API call when #51 exists. */
export function listQuoteRequests(filter: QueueFilter): QuoteRequest[] {
  return filter === 'unassigned' ? REQUESTS : []
}

/** How many requests a tab holds: always the length of its list, so the two cannot disagree. */
export function countQuoteRequests(filter: QueueFilter): number {
  return listQuoteRequests(filter).length
}
