import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { listPlanMessages } from '../../fixtures/conversation'
import type { Message } from '../../fixtures/trips'

import { Seal } from '../atoms/Seal'
import { ChatBubble } from '../molecules/ChatBubble'
import { ChatComposer } from '../molecules/ChatComposer'

const SUGGESTIONS = [
  ['suggestions.editDay', 'suggestions.editDayText'],
  ['suggestions.variant', 'suggestions.variantText'],
] as const

/**
 * The concierge conversation, docked at the bottom right on large screens. Below that it
 * sits at the end of the page and sticks to the bottom while scrolling, so it never hides
 * the page's last lines. It starts closed: open, it covers the page's own links.
 * Render it as the last child of the page.
 * A preview: messages stay on this page until the conversation API exists.
 */
export function ConversationDock({ version = 2 }: { version?: number }) {
  const { t } = useTranslation('concierge')
  const [open, setOpen] = useState(false)
  const [current, setCurrent] = useState(version)
  const [messages, setMessages] = useState<Message[]>(listPlanMessages)
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
      // Stands in for the concierge's answer until the conversation API exists.
      { from: 'novoya', text: t('done', { version: next }) },
    ])
    setCurrent(next)
    setDraft('')
  }

  return (
    <aside
      aria-label={t('dockLabel')}
      className="sticky bottom-2.5 z-10 mx-2.5 border border-line bg-white shadow-float lg:fixed lg:right-6 lg:bottom-5.5 lg:mx-0 lg:w-[390px]"
    >
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <Seal tone="ink" />
        <div className="grid flex-1">
          <b className="font-serif text-sm font-normal">{t('name')}</b>
          <small className="text-xs text-muted">{t('activeThread', { version: current })}</small>
        </div>
        <button
          type="button"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          className="grid size-11 place-items-center"
        >
          <span aria-hidden="true">{open ? '—' : '+'}</span>
          <span className="sr-only">{open ? t('collapse') : t('expand')}</span>
        </button>
      </div>
      {open && (
        <>
          <div
            role="log"
            aria-label={t('messages')}
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
                onClick={() => setDraft(t(text))}
                className="min-h-8 rounded-full border border-line bg-white px-2.5 text-xs"
              >
                {t(label)}
              </button>
            ))}
          </div>
          <ChatComposer value={draft} onChange={setDraft} onSend={send} placeholder={t('placeholder')} />
          <small className="hidden px-4 pb-3 text-xs text-muted lg:block">
            {t('note')}
          </small>
        </>
      )}
    </aside>
  )
}
