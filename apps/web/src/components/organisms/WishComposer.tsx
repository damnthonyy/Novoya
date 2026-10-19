import { type FormEvent, type KeyboardEvent, type Ref, useId } from 'react'
import { Trans, useTranslation } from 'react-i18next'

import { isApplePlatform } from '@/lib/platform'

type Props = {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  pending?: boolean
  /** Why the wish was not sent. */
  error?: string
  textareaRef?: Ref<HTMLTextAreaElement>
}

const kbd = 'rounded-[3px] border border-line px-1.5 py-0.5 font-sans'

/** The big white box where the client writes their wish. ⌘/Ctrl + Enter sends it. */
export function WishComposer({ value, onChange, onSubmit, pending = false, error, textareaRef }: Props) {
  const id = useId()
  const errorId = `${id}-error`
  const { t } = useTranslation('wish')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!pending) onSubmit()
  }
  const sendOnShortcut = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault()
      if (!pending) onSubmit()
    }
  }

  return (
    <form
      onSubmit={submit}
      aria-busy={pending}
      className="w-full rounded-[3px] border border-ink/10 bg-white p-[19px] text-left shadow-card md:w-[min(760px,90vw)] md:p-[25px]"
    >
      <label htmlFor={id} className="sr-only">
        {t('composerLabel')}
      </label>
      <textarea
        id={id}
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={sendOnShortcut}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        placeholder={t('placeholder')}
        className="h-[90px] w-full resize-none border-0 font-serif text-xl text-ink placeholder:text-muted"
      />
      {error && (
        <p id={errorId} role="alert" className="mb-2 text-sm text-danger">
          {error}
        </p>
      )}
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted">
          <Trans
            t={t}
            i18nKey="shortcut"
            values={{ key: isApplePlatform() ? '⌘' : 'Ctrl' }}
            components={[<kbd key="cmd" className={kbd} />, <kbd key="enter" className={kbd} />]}
          />
        </span>
        <button
          type="submit"
          aria-label={pending ? t('sending') : t('send')}
          disabled={pending}
          className="grid size-11 place-items-center rounded-full bg-coral text-xl text-ink transition hover:bg-coral-light disabled:opacity-60"
        >
          {pending ? (
            <span aria-hidden="true" className="size-4 animate-spin rounded-full border-2 border-ink border-t-transparent" />
          ) : (
            <span aria-hidden="true">↑</span>
          )}
        </button>
      </div>
    </form>
  )
}
