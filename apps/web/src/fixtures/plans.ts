// Demo data until the API exists (issue #76, GET /plans/{id}). A plan never has a price (#31).
import { PHOTOS } from './photos'

export type Moment = { time: string; period: string; title: string; text: string }

export type PlanDay = {
  number: number
  label: string
  date: string
  title: string
  text: string
  mood: string
  intro: string
  moments: Moment[]
}

export type Plan = {
  id: string
  version: number
  updatedLabel: string
  place: string
  tagline: string
  dates: string
  travellers: string
  tags: string[]
  photo: string
  photoAlt: string
  quoteId: string
  days: PlanDay[]
}

const moments: Moment[] = [
  { time: '08:30', period: 'Matin', title: 'Petit-déjeuner face à la baie', text: 'Un début de journée tranquille, sans départ précipité.' },
  { time: '11:00', period: 'Milieu de journée', title: 'Les criques de l’ouest', text: 'Route panoramique et baignade selon la météo.' },
  { time: '19:30', period: 'Soir', title: 'Retour au vieux port', text: 'Une table locale choisie selon vos envies du moment.' },
]

const DEMO: Plan = {
  id: 'chania',
  version: 2,
  updatedLabel: 'Mis à jour à l’instant',
  place: 'Chania,',
  tagline: 'au rythme de la mer.',
  dates: '12 → 19 mai 2026',
  travellers: '2 voyageurs',
  tags: ['calme', 'mer', 'cuisine locale'],
  photo: PHOTOS.crete,
  photoAlt: 'Eaux turquoise de Crète',
  quoteId: 'NV-2026-0182',
  days: [
    { number: 1, label: 'Jour 1', date: '12 mai', title: 'Arriver, respirer', text: 'Installation face à la mer, temps libre et première soirée douce dans le vieux port.', mood: 'Très doux', intro: 'Une arrivée sans hâte, pour poser les valises et regarder la mer.', moments },
    { number: 2, label: 'Jour 2', date: '13 mai', title: 'La côte au réveil', text: 'Petit-déjeuner au calme, criques de l’ouest et déjeuner tardif les pieds presque dans l’eau.', mood: 'Équilibré', intro: 'Une journée lumineuse, pensée pour laisser la mer donner le tempo.', moments },
    { number: 3, label: 'Jour 3', date: '14 mai', title: 'Chania, côté intime', text: 'Marché, ruelles et rencontre avec une guide locale. Soirée libre selon l’envie.', mood: 'Culture', intro: 'La ville à pied, avec quelqu’un qui la connaît de l’intérieur.', moments },
    { number: 4, label: 'Jour 4', date: '15 mai', title: 'Une journée sans montre', text: 'Plage confidentielle et table de produits crétois. Rien d’autre au programme.', mood: 'Très doux', intro: 'Rien à prévoir, tout à savourer.', moments },
  ],
}

/** The plan to show. Replace with the API call when GET /plans/{id} exists. */
export function getPlan(planId: string): Plan | undefined {
  return planId === DEMO.id ? DEMO : undefined
}

export const DEMO_PLAN_ID = DEMO.id
