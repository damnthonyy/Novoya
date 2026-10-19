import { useId, useState } from 'react'

import { Button } from '../atoms/Button'

type Decision = 'accepted' | 'refused'

/**
 * Accept or refuse the agency's offer, with an optional comment.
 * `onDecide` is where the page sends the decision; the panel then shows the confirmation.
 */
export function QuoteDecision({ onDecide }: { onDecide?: (decision: Decision, comment: string) => void }) {
  const [comment, setComment] = useState('')
  const [decision, setDecision] = useState<Decision | null>(null)
  const id = useId()

  const decide = (value: Decision) => {
    onDecide?.(value, comment)
    setDecision(value)
  }

  return (
    <aside aria-labelledby={`${id}-title`} className="bg-ink p-7 text-white md:sticky md:top-30">
      <h2 id={`${id}-title`} className="mb-3 text-[25px] tracking-normal">
        Votre décision
      </h2>
      {decision ? (
        <p role="status" className="text-sm leading-relaxed">
          {decision === 'accepted'
            ? 'Merci ! Votre conseillère confirme les réservations et revient vers vous très vite.'
            : 'C’est noté. Votre conseillère peut vous proposer une autre version si vous le souhaitez.'}
        </p>
      ) : (
        <>
          <p className="text-sm leading-relaxed text-white/70">
            Votre conseillère reste disponible avant toute confirmation.
          </p>
          <label htmlFor={id} className="sr-only">
            Une question ou un commentaire ? (facultatif)
          </label>
          <textarea
            id={id}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Une question ou un commentaire ? (facultatif)"
            className="my-4 h-22 w-full resize-none border border-white/20 bg-white/10 p-3 text-sm text-white placeholder:text-white/60"
          />
          <Button variant="coral" className="w-full" onClick={() => decide('accepted')}>
            Accepter l’offre
          </Button>
          <Button variant="glass" className="mt-2.5 w-full" onClick={() => decide('refused')}>
            Refuser l’offre
          </Button>
        </>
      )}
      <small className="mt-5 block text-xs leading-normal text-white/60">
        Aucun nom de prestataire n’apparaît sur l’offre.
      </small>
    </aside>
  )
}
