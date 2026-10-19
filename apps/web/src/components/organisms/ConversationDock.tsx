import { useEffect, useState } from 'react'

import { Seal } from '../atoms/Seal'
import { ChatBubble } from '../molecules/ChatBubble'
import { ChatComposer } from '../molecules/ChatComposer'

type Message = { from: 'you' | 'novoya'; text: string }

const START: Message[] = [
  { from: 'novoya', text: 'Voici votre aperçu. J’ai gardé un rythme très doux et laissé le jour 4 presque libre.' },
  { from: 'you', text: 'J’aimerais un peu plus de culture, sans surcharger.' },
  { from: 'novoya', text: 'Bien sûr. J’ai ajouté une rencontre locale le jour 3. L’aperçu est maintenant en version 2.' },
]

const SUGGESTIONS = [
  ['Modifier un jour', 'Rendre le jour 4 plus actif'],
  ['Créer une variante', 'Créer une variante plus culturelle'],
]

/**
 * The concierge conversation, docked at the bottom right on large screens. Below that it
 * sits at the end of the page and sticks to the bottom while scrolling, so it never hides
 * the page's last lines. It starts closed: open, it covers the page's own links.
 * Render it as the last child of the page.
 * A preview: messages stay on this page until the conversation API exists.
 */
export function ConversationDock({ version = 2 }: { version?: number }) {
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState(version)
  const [messages, setMessages] = useState(START)
  const [draft, setDraft] = useState('')

  // Keep focused links and buttons from scrolling under the docked bar.
  useEffect(() => {
    const root = document.documentElement
    root.style.scrollPaddingBottom = '7rem'
    return () => {
      root.style.scrollPaddingBottom = ''
    }
  }, [])

  const send = () => {
    if (!draft.trim()) return
    const next = current + 1
    setMessages([
      ...messages,
      { from: 'you', text: draft },
      { from: 'novoya', text: `C’est fait. La version ${next} de votre aperçu intègre cette demande.` },
    ])
    setCurrent(next)
    setDraft('')
  }

  return (
    <aside
      aria-label="Conversation avec le concierge"
      className="sticky bottom-2.5 z-10 mx-2.5 border border-line bg-white shadow-float lg:fixed lg:right-6 lg:bottom-5.5 lg:mx-0 lg:w-[390px]"
    >
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <Seal tone="ink" />
        <div className="grid flex-1">
          <b className="font-serif text-sm font-normal">Concierge Novoya</b>
          <small className="text-xs text-muted">Fil actif · aperçu v{current}</small>
        </div>
        <button
          type="button"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          className="grid size-11 place-items-center"
        >
          <span aria-hidden="true">{open ? '—' : '+'}</span>
          <span className="sr-only">{open ? 'Réduire la conversation' : 'Ouvrir la conversation'}</span>
        </button>
      </div>
      {open && (
        <>
          <div
            role="log"
            aria-label="Messages"
            tabIndex={0}
            className="max-h-24 overflow-auto bg-paper px-4 py-4 lg:max-h-40">
            {messages.slice(-4).map((message, i) => (
              <ChatBubble key={`${i}-${message.text}`} {...message} />
            ))}
          </div>
          <div className="hidden gap-1.5 px-4 pt-2 lg:flex">
            {SUGGESTIONS.map(([label, text]) => (
              <button
                key={label}
                type="button"
                onClick={() => setDraft(text!)}
                className="min-h-8 rounded-full border border-line bg-white px-2.5 text-xs"
              >
                {label}
              </button>
            ))}
          </div>
          <ChatComposer value={draft} onChange={setDraft} onSend={send} placeholder="Affiner, poser une question…" />
          <small className="hidden px-4 pb-3 text-xs text-muted lg:block">
            L’aperçu peut évoluer à chaque message. Aucun prix n’est généré.
          </small>
        </>
      )}
    </aside>
  )
}
