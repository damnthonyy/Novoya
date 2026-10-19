import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { listPlanMessages } from '../../fixtures/conversation'
import type { Message } from '../../fixtures/trips'

import { Seal } from '../atoms/Seal'
import { ChatBubble } from '../molecules/ChatBubble'
import { ChatComposer } from '../molecules/ChatComposer'

/**
 * The concierge conversation, docked at the bottom right on large screens. Below that it
 * sits at the end of the page and sticks to the bottom while scrolling, so it never hides
 * the page's last lines. It starts closed: open, it covers the page's own links.
 * Render it as the last child of the page.
 * A preview: it shows the demo messages, and sending is disabled until the conversation API exists.
 */
export function ConversationDock({ version = 2 }: { version?: number }) {
  const { t } = useTranslation('concierge')
  const [open, setOpen] = useState(false)
  const [messages] = useState<Message[]>(listPlanMessages)
  const [draft, setDraft] = useState('')

  // Keep focused links and buttons from scrolling under the docked bar.
  useEffect(() => {
    const root = document.documentElement
    root.style.scrollPaddingBottom = '7rem'
    return () => {
      root.style.scrollPaddingBottom = ''
    }
  }, [])

  return (
    <aside
      aria-label={t('dockLabel')}
      className="sticky bottom-2.5 z-10 mx-2.5 border border-line bg-white shadow-float lg:fixed lg:right-6 lg:bottom-5.5 lg:mx-0 lg:w-[390px]"
    >
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <Seal tone="ink" />
        <div className="grid flex-1">
          <b className="font-serif text-sm font-normal">{t('name')}</b>
          <small className="text-xs text-muted">{t('activeThread', { version })}</small>
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
          <ChatComposer value={draft} onChange={setDraft} onSend={() => {}} placeholder={t('placeholder')} disabled />
          <small className="block px-4 pb-3 text-xs text-muted">{t('unavailable')}</small>
        </>
      )}
    </aside>
  )
}
