import { useId, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '../atoms/Button'

export type Decision = 'accepted' | 'refused'

/**
 * Accept or refuse the agency's offer, with an optional comment. The page sends the decision
 * through `onDecide`. Without it (no API yet, #54) the buttons are disabled and say why,
 * so nobody believes they answered a real offer.
 */
export function QuoteDecision({ onDecide }: { onDecide?: (decision: Decision, comment: string) => void }) {
  const { t } = useTranslation('quote')
  const [comment, setComment] = useState('')
  const id = useId()
  const unavailable = !onDecide

  return (
    <aside aria-labelledby={`${id}-title`} className="bg-ink p-7 text-white md:sticky md:top-30">
      <h2 id={`${id}-title`} className="mb-3 text-[25px] tracking-normal">
        {t('decision.title')}
      </h2>
      <p className="text-sm leading-relaxed text-white/70">{t('decision.intro')}</p>
      <label htmlFor={id} className="sr-only">
        {t('decision.commentLabel')}
      </label>
      <textarea
        id={id}
        value={comment}
        disabled={unavailable}
        onChange={(event) => setComment(event.target.value)}
        placeholder={t('decision.commentLabel')}
        className="my-4 h-22 w-full resize-none border border-white/20 bg-white/10 p-3 text-sm text-white placeholder:text-white/60 disabled:opacity-60"
      />
      <Button variant="coral" className="w-full" disabled={unavailable} onClick={() => onDecide?.('accepted', comment)}>
        {t('decision.accept')}
      </Button>
      <Button variant="glass" className="mt-2.5 w-full" disabled={unavailable} onClick={() => onDecide?.('refused', comment)}>
        {t('decision.refuse')}
      </Button>
      {unavailable && <p className="mt-4 text-sm text-white/80">{t('decision.unavailable')}</p>}
      <small className="mt-5 block text-xs leading-normal text-white/60">{t('decision.noSupplier')}</small>
    </aside>
  )
}
