// Demo data until the API exists (issue #76 for plans, #50 for quote requests).
import { PHOTOS } from './photos'

export type Message = { from: 'you' | 'novoya'; text: string }

export type Thread = {
  id: string
  photo: string
  status: string
  /** The status that needs the client's attention. */
  highlight?: boolean
  place: string
  title: string
  version: string
  time: string
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
  { id: 'chania', photo: PHOTOS.crete, status: 'Offre de l’agence envoyée', highlight: true, place: 'Grèce · 12—19 mai 2026', title: 'Chania, au rythme de la mer', version: 'Aperçu v2 · 12 messages', time: 'Aujourd’hui, 10:42', planId: 'chania', messages: chaniaMessages },
  { id: 'marrakech', photo: PHOTOS.marrakech, status: 'Aperçu proposé', place: 'Maroc · Dates à préciser', title: 'Marrakech, derrière les portes', version: 'Aperçu v1 · 8 messages', time: 'Hier, 18:16', messages: [{ from: 'you', text: 'Quelques jours au soleil, entre culture et calme.' }, { from: 'novoya', text: 'Voici un premier aperçu dans un riad de la médina.' }] },
  { id: 'biarritz', photo: PHOTOS.biarritz, status: 'En discussion', place: 'France · Juin 2026', title: 'Biarritz, plein ouest', version: 'Brouillon · 5 messages', time: '19 oct., 09:30', messages: [{ from: 'you', text: 'Une parenthèse sportive face à l’océan.' }] },
  { id: 'milos', photo: PHOTOS.hero, status: 'Acceptée', place: 'Grèce · Septembre 2026', title: 'Milos, lumière des Cyclades', version: 'Aperçu v3 · 21 messages', time: '2 sept., 14:12', messages: [{ from: 'novoya', text: 'Votre voyage est confirmé. Bon départ !' }] },
  { id: 'essaouira', photo: PHOTOS.marrakech, status: 'Refusée', place: 'Maroc · Mars 2026', title: 'Essaouira, au gré du vent', version: 'Aperçu v2 · 14 messages', time: '8 mars, 11:05', messages: [{ from: 'you', text: 'Finalement, je préfère d’autres dates.' }] },
]

/** The client's trips and conversations. Replace with the API call when it exists. */
export function listThreads(): Thread[] {
  return THREADS
}
