// Demo data until the API exists (issue #51, agent queue).

export type QuoteRequest = {
  id: string
  client: string
  title: string
  wish: string
  budget: string
  dates: string
  travellers: number
  received: string
}

const REQUESTS: QuoteRequest[] = [
  { id: 'r1', client: 'Camille Martin', title: 'Chania, au rythme de la mer', wish: 'Une semaine calme, de bonnes tables et beaucoup de mer.', budget: '3 500 €', dates: '12—19 mai', travellers: 2, received: 'Il y a 1 h' },
  { id: 'r2', client: 'Nora Bernard', title: 'Marrakech, derrière les portes', wish: 'Un riad au calme, la médina à pied.', budget: '2 200 €', dates: '3—7 juin', travellers: 2, received: 'Il y a 2 h' },
  { id: 'r3', client: 'Louis Perrin', title: 'Biarritz, plein ouest', wish: 'Du surf le matin, l’océan le soir.', budget: '1 800 €', dates: '18—21 juin', travellers: 1, received: 'Il y a 3 h' },
]

export type QueueFilter = 'unassigned' | 'in_progress' | 'decided'

export const QUEUE_COUNTS: Record<QueueFilter, number> = { unassigned: 3, in_progress: 7, decided: 12 }

/** The quote requests in one tab of the queue. Replace with the API call when #51 exists. */
export function listQuoteRequests(filter: QueueFilter): QuoteRequest[] {
  return filter === 'unassigned' ? REQUESTS : []
}
