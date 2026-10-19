// Demo data until the API exists (issue #54, see the quote and accept or reject it).

// Line labels are written by the agent. Amounts are whole euros.
export type QuoteLine = { label: string; amount: number }

export type Quote = {
  id: string
  destination: string
  agentName: string
  validDays: number
  /** ISO date. */
  issuedAt: string
  startDate: string
  endDate: string
  travellers: number
  days: number
  nights: number
  lines: QuoteLine[]
  total: number
  budget: number
}

const DEMO: Quote = {
  id: 'NV-2026-0182',
  destination: 'Chania',
  agentName: 'Léa',
  validDays: 7,
  issuedAt: '2026-10-20',
  startDate: '2026-05-12',
  endDate: '2026-05-19',
  travellers: 2,
  days: 7,
  nights: 6,
  lines: [
    { label: 'Hébergement · 6 nuits', amount: 1860 },
    { label: 'Expériences & visites', amount: 420 },
    { label: 'Transferts sur place', amount: 280 },
    { label: 'Accompagnement Novoya', amount: 190 },
  ],
  total: 2750,
  budget: 3500,
}

/** The quote to show. Replace with the API call when #54 exists. */
export function getQuote(quoteId: string): Quote | undefined {
  return quoteId === DEMO.id ? DEMO : undefined
}
