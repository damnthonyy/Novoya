import { useId } from 'react'
import { useTranslation } from 'react-i18next'

import { cn } from '@/lib/utils'

type Props = {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  placeholder: string
  /** Shown but not usable, e.g. until the conversation API exists. */
  disabled?: boolean
  className?: string
}

/** A message field with a round send button. Enter sends, Shift+Enter adds a line. */
export function ChatComposer({ value, onChange, onSend, placeholder, disabled = false, className }: Props) {
  const id = useId()
  const { t } = useTranslation('concierge')
  return (
    <form
      className={cn('flex items-end gap-2 px-4 py-2.5', className)}
      onSubmit={(event) => {
        event.preventDefault()
        if (!disabled) onSend()
      }}
    >
      <label htmlFor={id} className="sr-only">
        {placeholder}
      </label>
      <textarea
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault()
            if (!disabled) onSend()
          }
        }}
        placeholder={placeholder}
        disabled={disabled}
        className="h-11 w-full resize-none border-0 bg-ivory p-3 text-xs placeholder:text-muted focus-visible:outline-2 disabled:opacity-60"
      />
      <button
        type="submit"
        aria-label={t('send')}
        disabled={disabled}
        className="grid size-11 shrink-0 place-items-center rounded-full bg-coral text-ink disabled:opacity-50"
      >
        <span aria-hidden="true">↑</span>
      </button>
    </form>
  )
}
