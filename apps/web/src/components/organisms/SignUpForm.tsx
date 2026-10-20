import { useForm } from '@tanstack/react-form'
import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Button } from '../atoms/Button'
import { Divider } from '../atoms/Divider'
import { GoogleButton } from '../molecules/GoogleButton'
import { TextField } from '../molecules/TextField'

type Props = {
  /** Where "Continue with Google" goes. */
  googleHref: string
  onSubmit: (account: { email: string; password: string }) => void
  pending?: boolean
  /** Why the last attempt failed: next to its field, or for the whole form. */
  errors?: { email?: string; password?: string; form?: string }
}

/** Google, or a new account with an e-mail and a password. */
export function SignUpForm({ googleHref, onSubmit, pending = false, errors = {} }: Props) {
  const { t } = useTranslation('auth')
  const form = useForm({
    defaultValues: { email: '', password: '' },
    onSubmit: ({ value }) => {
      if (!pending) onSubmit({ email: value.email.trim(), password: value.password })
    },
  })

  return (
    <>
      <div className="my-5">
        <GoogleButton href={googleHref} />
      </div>
      <Divider label={t('orWithEmail')} />
      <form
        onSubmit={(event) => {
          event.preventDefault()
          void form.handleSubmit()
        }}
      >
        <form.Field name="email">
          {(field) => (
            <TextField
              label={t('email')}
              type="email"
              name={field.name}
              autoComplete="email"
              required
              placeholder={t('emailPlaceholder')}
              value={field.state.value}
              onChange={field.handleChange}
              onBlur={field.handleBlur}
              error={errors.email}
            />
          )}
        </form.Field>
        <form.Field name="password">
          {(field) => (
            <TextField
              label={t('password')}
              type="password"
              name={field.name}
              autoComplete="new-password"
              required
              hint={t('signUp.passwordHint')}
              value={field.state.value}
              onChange={field.handleChange}
              onBlur={field.handleBlur}
              error={errors.password}
            />
          )}
        </form.Field>
        {errors.form && (
          <p role="alert" className="mb-4 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <Button type="submit" size="lg" className="mt-2 w-full" disabled={pending}>
          {pending ? t('signUp.submitting') : t('signUp.submit')} <span aria-hidden="true">↗</span>
        </Button>
      </form>
      <p className="mt-6 text-center text-sm">
        {t('signUp.haveAccount')}{' '}
        <Link to="/login" className="underline underline-offset-4">
          {t('signUp.signInLink')}
        </Link>
      </p>
    </>
  )
}
