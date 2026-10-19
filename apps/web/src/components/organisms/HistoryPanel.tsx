import { Link } from '@tanstack/react-router'
import { useState } from 'react'

import { Seal } from '../atoms/Seal'
import { ChatBubble } from '../molecules/ChatBubble'
import { ChatComposer } from '../molecules/ChatComposer'

type Props = {
  title: string
  version: string
  planId?: string
  messages: { from: 'you' | 'novoya'; text: string }[]
}

/** The full conversation of one trip, with a link to its current plan. */
export function HistoryPanel({ title, version, planId, messages }: Props) {
  const [draft, setDraft] = useState('')
  return (
    <section aria-label={`Historique : ${title}`} className="mt-6 flex min-h-[540px] flex-col border border-line bg-white lg:mt-0">
      <div className="flex items-center gap-3 border-b border-line p-4.5">
        <Seal tone="ink" />
        <div className="flex-1">
          <small className="text-xs tracking-[0.14em] text-muted">HISTORIQUE COMPLET</small>
          <h2 className="my-1 text-xl tracking-normal">{title}</h2>
          <p className="m-0 text-xs text-muted">{version}</p>
        </div>
      </div>
      {planId && (
        <div className="mx-4.5 mt-4 grid grid-cols-[1fr_auto] items-center bg-ivory p-3">
          <span className="font-serif">{version.split(' · ')[0]}</span>
          <Link
            to="/plans/$planId"
            params={{ planId }}
            className="col-start-2 row-span-2 flex min-h-11 items-center text-xs text-ink underline underline-offset-4"
          >
            Voir l’aperçu →
          </Link>
          <small className="text-xs text-muted">Version actuelle</small>
        </div>
      )}
      <div role="log" aria-label="Messages" tabIndex={0} className="mx-4.5 mt-3 h-[300px] overflow-auto bg-paper px-4.5 py-4">
        {messages.map((message, i) => (
          <ChatBubble key={`${i}-${message.text}`} {...message} />
        ))}
      </div>
      <ChatComposer value={draft} onChange={setDraft} onSend={() => setDraft('')} placeholder="Reprendre cette conversation…" />
      <small className="px-4.5 pb-4 text-xs text-muted">Le fil reprend exactement là où vous l’avez laissé.</small>
    </section>
  )
}
