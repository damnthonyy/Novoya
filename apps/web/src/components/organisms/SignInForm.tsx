import { useForm } from '@tanstack/react-form'

import { Divider } from '../atoms/Divider'
import { GoogleButton } from '../molecules/GoogleButton'
import { TextField } from '../molecules/TextField'

type SignInValues = { email: string; password: string }

type SignInFormProps = {
  onSubmit: (values: SignInValues) => void | Promise<void>
  onGoogle?: () => void
  error?: string
}

export function SignInForm({ onSubmit, onGoogle, error }: SignInFormProps) {
  const form = useForm({
    defaultValues: { email: '', password: '' },
    onSubmit: async ({ value }) => {
      await onSubmit(value)
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <GoogleButton onClick={onGoogle} />
      <Divider label="ou avec votre e-mail" />

      <form
        className="flex flex-col gap-5"
        onSubmit={(e) => {
          e.preventDefault()
          e.stopPropagation()
          form.handleSubmit()
        }}
      >
        <form.Field name="email">
          {(field) => (
            <TextField
              label="E-mail"
              type="email"
              value={field.state.value}
              onChange={field.handleChange}
              placeholder="camille@exemple.fr"
            />
          )}
        </form.Field>

        <form.Field name="password">
          {(field) => (
            <TextField
              label="Mot de passe"
              type="password"
              value={field.state.value}
              onChange={field.handleChange}
              error={error}
            />
          )}
        </form.Field>

        <a href="/forgot-password" className="self-end text-sm text-ink underline">
          Mot de passe oublié ?
        </a>

        <button
          type="submit"
          className="rounded-full bg-ink px-6 py-3.5 text-base text-white"
        >
          Se connecter
        </button>
      </form>

      <p className="text-center text-sm text-ink">
        Pas encore de compte ?{' '}
        <a href="/signup" className="underline">
          S’inscrire
        </a>
      </p>
    </div>
  )
}