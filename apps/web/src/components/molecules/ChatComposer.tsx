import { useId } from 'react'

import { cn } from '@/lib/utils'

type Props = {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  placeholder: string
  className?: string
}

/** A message field with a round send button. Enter sends, Shift+Enter adds a line. */
export function ChatComposer({ value, onChange, onSend, placeholder, className }: Props) {
  const id = useId()
  return (
    <form
      className={cn('flex items-end gap-2 px-4 py-2.5', className)}
      onSubmit={(event) => {
        event.preventDefault()
        onSend()
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
            onSend()
          }
        }}
        placeholder={placeholder}
        className="h-11 w-full resize-none border-0 bg-ivory p-3 text-xs placeholder:text-muted focus-visible:outline-2"
      />
      <button
        type="submit"
        aria-label="Envoyer"
        className="grid size-11 shrink-0 place-items-center rounded-full bg-coral text-ink"
      >
        <span aria-hidden="true">↑</span>
      </button>
    </form>
  )
}
