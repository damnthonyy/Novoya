// Demo data until the conversation API exists: the concierge's first messages on a plan.
// They come from the LLM, already in the user's language.
import type { Message } from './trips'

const START: Message[] = [
  { from: 'novoya', text: 'Voici votre aperçu. J’ai gardé un rythme très doux et laissé le jour 4 presque libre.' },
  { from: 'you', text: 'J’aimerais un peu plus de culture, sans surcharger.' },
  { from: 'novoya', text: 'Bien sûr. J’ai ajouté une rencontre locale le jour 3. L’aperçu est maintenant en version 2.' },
]

/** The conversation so far on a plan. Replace with the API call when it exists. */
export function listPlanMessages(): Message[] {
  return START
}
