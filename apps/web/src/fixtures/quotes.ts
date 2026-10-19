// Demo data until the API exists (issue #54, see the quote and accept or reject it).

export type QuoteLine = { label: string; amount: string }

export type Quote = {
  id: string
  place: string
  agentName: string
  validity: string
  issued: string
  dates: string
  travellers: string
  length: string
  lines: QuoteLine[]
  total: string
  budget: string
}

const DEMO: Quote = {
  id: 'NV-2026-0182',
  place: 'à Chania.',
  agentName: 'Léa',
  validity: 'Valable 7 jours',
  issued: 'Émise le 20 octobre 2026',
  dates: '12 → 19 mai 2026',
  travellers: '2 voyageurs',
  length: '7 jours / 6 nuits',
  lines: [
    { label: 'Hébergement · 6 nuits', amount: '1 860 €' },
    { label: 'Expériences & visites', amount: '420 €' },
    { label: 'Transferts sur place', amount: '280 €' },
    { label: 'Accompagnement Novoya', amount: '190 €' },
  ],
  total: '2 750 €',
  budget: '3 500 €',
}

/** The quote to show. Replace with the API call when #54 exists. */
export function getQuote(quoteId: string): Quote | undefined {
  return quoteId === DEMO.id ? DEMO : undefined
}
