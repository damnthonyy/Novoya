import { type FormEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '../atoms/Button'
import { Input } from '../atoms/Input'
import { Field } from '../molecules/Field'

type Props = {
  onSubmit: (credentials: { email: string; password: string }) => void
  pending?: boolean
  /** Why the last attempt failed. */
  error?: string
}

/** E-mail and password sign-in. The page sends the request and says what went wrong. */
export function PasswordSignInForm({ onSubmit, pending = false, error }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [shown, setShown] = useState(false)
  const { t } = useTranslation('auth')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!pending) onSubmit({ email: email.trim(), password })
  }

  return (
    <form onSubmit={submit}>
      <Field label={t('email')}>
        {({ id, describedBy }) => (
          <Input
            id={id}
            aria-describedby={describedBy}
            type="email"
            autoComplete="email"
            required
            placeholder={t('emailPlaceholder')}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        )}
      </Field>
      <Field label={t('password')}>
        {({ id, describedBy }) => (
          <div className="relative">
            <Input
              id={id}
              aria-describedby={describedBy}
              type={shown ? 'text' : 'password'}
              autoComplete="current-password"
              required
              className="pr-24"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              aria-pressed={shown}
              onClick={() => setShown(!shown)}
              className="absolute top-1/2 right-1 min-h-11 -translate-y-1/2 px-3 text-xs underline underline-offset-4"
            >
              {shown ? t('hidePassword') : t('showPassword')}
            </button>
          </div>
        )}
      </Field>
      {error && (
        <p role="alert" className="mb-4 text-sm text-danger">
          {error}
        </p>
      )}
      <Button type="submit" size="lg" className="mt-2 w-full" disabled={pending}>
        {pending ? t('signingIn') : t('submit')} <span aria-hidden="true">↗</span>
      </Button>
    </form>
  )
}
