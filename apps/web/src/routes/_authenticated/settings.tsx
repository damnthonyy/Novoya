import { useMutation } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { changePasswordMutation } from '../../api/generated/@tanstack/react-query.gen'
import { Eyebrow } from '../../components/atoms/Eyebrow'
import { ChangePasswordForm } from '../../components/organisms/ChangePasswordForm'
import { AppShell } from '../../components/templates/AppShell'
import { useAccountErrors } from '../-accountErrors'

export const Route = createFileRoute('/_authenticated/settings')({
  component: SettingsPage,
})

function SettingsPage() {
  const { me } = Route.useRouteContext()
  const { t } = useTranslation('settings')
  const change = useMutation(changePasswordMutation())
  const errors = useAccountErrors(change.error)
  const hasPassword = me.sign_in_methods.includes('password')

  return (
    <AppShell>
      <main className="px-5 pt-14 pb-22 md:px-[8vw] md:pt-20">
        <Eyebrow>{t('eyebrow')}</Eyebrow>
        <h1 className="mb-3 text-[55px] leading-none md:text-[75px]">{t('title')}</h1>
        <p className="text-muted">
          <span className="sr-only">{t('email')} </span>
          {me.email}
        </p>
        <section aria-labelledby="password-title" className="mt-12 max-w-[420px]">
          <h2 id="password-title" className="mb-2 text-[30px] leading-tight">
            {t('passwordTitle')}
          </h2>
          {hasPassword ? (
            <ChangePasswordForm
              onSubmit={({ currentPassword, newPassword }) =>
                change.mutateAsync({ body: { current_password: currentPassword, new_password: newPassword } })
              }
              pending={change.isPending}
              errors={{ currentPassword: errors.currentPassword, newPassword: errors.password, form: errors.form }}
              success={change.isSuccess ? t('changed') : undefined}
            />
          ) : (
            <>
              <p className="mb-4 text-muted">{t('googleOnly')}</p>
              <Link to="/forgot-password" className="underline underline-offset-4">
                {t('setPassword')}
              </Link>
            </>
          )}
        </section>
      </main>
    </AppShell>
  )
}
