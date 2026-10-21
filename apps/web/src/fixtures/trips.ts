// Demo data until the API exists (issue #76 for plans, #50 for quote requests).
import { daysFromToday, monthFromToday, monthOf } from './demoDates'
import { PHOTOS } from './photos'

export type Message = { from: 'you' | 'novoya'; text: string }

/** Where the trip stands: the page translates it. */
export type ThreadStatus = 'offer_sent' | 'preview_proposed' | 'in_discussion' | 'accepted' | 'refused'

/** The trip's dates: a range, a month (dates not set yet), or nothing yet. */
export type ThreadDates = { start: string; end: string } | { month: string } | null

export type Thread = {
  id: string
  photo: string
  status: ThreadStatus
  /** The status that needs the client's attention. */
  highlight?: boolean
  country: string
  dates: ThreadDates
  title: string
  /** The current preview's version, or null for a draft. */
  version: number | null
  messageCount: number
  /** ISO date and time of the last message. */
  updatedAt: string
  planId?: string
  messages: Message[]
}

const chaniaMessages: Message[] = [
  { from: 'you', text: 'Une semaine calme au bord de la mer en mai, avec de bons petits-déjeuners.' },
  { from: 'novoya', text: 'J’ai trouvé une possibilité à Chania auprès de nos partenaires actifs. Souhaitez-vous un rythme très doux ou quelques journées plus remplies ?' },
  { from: 'you', text: 'Très doux, mais avec un peu de culture locale.' },
  { from: 'novoya', text: 'Votre aperçu est prêt. J’ai laissé de vrais temps libres et ajouté une rencontre locale le troisième jour.' },
  { from: 'you', text: 'Peut-on rendre le jour 4 un peu plus actif ?' },
]

const THREADS: Thread[] = [
  { id: 'chania', photo: PHOTOS.crete, status: 'offer_sent', highlight: true, country: 'Grèce', dates: { start: daysFromToday(60), end: daysFromToday(66) }, title: 'Chania, au rythme de la mer', version: 2, messageCount: 12, updatedAt: '2026-10-19T10:42:00Z', planId: 'chania', messages: chaniaMessages },
  { id: 'marrakech', photo: PHOTOS.marrakech, status: 'preview_proposed', country: 'Maroc', dates: null, title: 'Marrakech, derrière les portes', version: 1, messageCount: 8, updatedAt: '2026-10-18T18:16:00Z', messages: [{ from: 'you', text: 'Quelques jours au soleil, entre culture et calme.' }, { from: 'novoya', text: 'Voici un premier aperçu dans un riad de la médina.' }] },
  { id: 'biarritz', photo: PHOTOS.biarritz, status: 'in_discussion', country: 'France', dates: { month: monthOf(daysFromToday(97)) }, title: 'Biarritz, plein ouest', version: null, messageCount: 5, updatedAt: '2026-10-19T09:30:00Z', messages: [{ from: 'you', text: 'Une parenthèse sportive face à l’océan.' }] },
  { id: 'milos', photo: PHOTOS.hero, status: 'accepted', country: 'Grèce', dates: { month: monthFromToday(1) }, title: 'Milos, lumière des Cyclades', version: 3, messageCount: 21, updatedAt: '2026-09-02T14:12:00Z', messages: [{ from: 'novoya', text: 'Votre voyage est confirmé. Bon départ !' }] },
  { id: 'essaouira', photo: PHOTOS.marrakech, status: 'refused', country: 'Maroc', dates: { month: '2026-03-01' }, title: 'Essaouira, au gré du vent', version: 2, messageCount: 14, updatedAt: '2026-03-08T11:05:00Z', messages: [{ from: 'you', text: 'Finalement, je préfère d’autres dates.' }] },
]

/** The client's trips and conversations. Replace with the API call when it exists. */
export function listThreads(): Thread[] {
  return THREADS
}
