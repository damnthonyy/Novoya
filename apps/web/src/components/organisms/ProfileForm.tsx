import { useForm } from '@tanstack/react-form'
import { useTranslation } from 'react-i18next'

import type { Locale } from '../../domain/i18n/locale'
import { Button } from '../atoms/Button'
import { SelectField } from '../molecules/SelectField'
import { TextField } from '../molecules/TextField'

export type Profile = { firstName: string; lastName: string; locale: Locale }

type Props = {
  /** What is stored now. */
  profile: Profile
  /** Shown, never sent: it is the sign-in identity. */
  email: string
  /** Resolves with what the API stored, which the form then shows. Rejects on failure. */
  onSubmit: (profile: Profile) => Promise<Profile>
  pending?: boolean
  /** Why the last save failed: next to its field, or for the whole form. */
  errors?: { firstName?: string; lastName?: string; form?: string }
  /** Said once the save worked. */
  success?: string
}

/** The client's first name, last name and language, and their e-mail, read-only. */
export function ProfileForm({ profile, email, onSubmit, pending = false, errors = {}, success }: Props) {
  const { t } = useTranslation('profile')
  const form = useForm({
    defaultValues: profile,
    onSubmit: async ({ value, formApi }) => {
      if (pending) return
      try {
        formApi.reset(await onSubmit(value))
      } catch {
        // The page shows why; keep what was typed.
      }
    },
  })

  return (
    <form
      aria-label={t('title')}
      className="max-w-[420px]"
      onSubmit={(event) => {
        event.preventDefault()
        void form.handleSubmit()
      }}
    >
      <form.Field name="firstName">
        {(field) => (
          <TextField
            label={t('firstName')}
            name={field.name}
            autoComplete="given-name"
            required
            maxLength={100}
            value={field.state.value}
            onChange={field.handleChange}
            onBlur={field.handleBlur}
            error={errors.firstName}
          />
        )}
      </form.Field>
      <form.Field name="lastName">
        {(field) => (
          <TextField
            label={t('lastName')}
            name={field.name}
            autoComplete="family-name"
            required
            maxLength={100}
            value={field.state.value}
            onChange={field.handleChange}
            onBlur={field.handleBlur}
            error={errors.lastName}
          />
        )}
      </form.Field>
      <TextField label={t('email')} type="email" value={email} onChange={() => {}} readOnly hint={t('emailHint')} />
      <form.Field name="locale">
        {(field) => (
          <SelectField<Locale>
            label={t('language')}
            value={field.state.value}
            options={[
              { value: 'en', label: 'English' },
              { value: 'fr', label: 'Français' },
            ]}
            onChange={(value) => {
              if (value) field.handleChange(value)
            }}
          />
        )}
      </form.Field>
      {errors.form && (
        <p role="alert" className="mb-4 text-sm text-danger">
          {errors.form}
        </p>
      )}
      {success && (
        <p role="status" className="mb-4 text-sm">
          {success}
        </p>
      )}
      <Button type="submit" className="mt-2 w-full sm:w-auto" disabled={pending}>
        {pending ? t('saving') : t('save')}
      </Button>
    </form>
  )
}
