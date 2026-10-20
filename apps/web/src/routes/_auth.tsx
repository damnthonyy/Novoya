import { createFileRoute, Link, Outlet } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Logo } from '../components/atoms/Logo'
import { AuthMedia } from '../components/organisms/AuthMedia'
import { AuthTemplate } from '../components/templates/AuthTemplate'

// The account pages, signed in or not: sign-in, sign-up, e-mail confirmation, lost password.
export const Route = createFileRoute('/_auth')({
  component: AuthLayout,
})

function AuthLayout() {
  const { t } = useTranslation('auth')
  const { t: tCommon } = useTranslation()
  return (
    <AuthTemplate
      media={
        <AuthMedia
          image="/images/aegean-boat"
          imageAlt={t('imageAlt')}
          logo={
            <Link to="/" aria-label={tCommon('homeLink')} className="flex min-h-11 items-center no-underline">
              <Logo light />
            </Link>
          }
          quote={t('quote')}
          caption={t('caption')}
        />
      }
    >
      <Outlet />
    </AuthTemplate>
  )
}
