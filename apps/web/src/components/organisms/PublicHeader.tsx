import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Button } from '../atoms/Button'
import { Logo } from '../atoms/Logo'

/** The header over the landing page's photo, for visitors. */
export function PublicHeader({ signedIn = false }: { signedIn?: boolean }) {
  const { t } = useTranslation('header')
  const { t: tCommon } = useTranslation()
  return (
    <header className="absolute inset-x-0 top-0 z-10 flex h-18 items-center justify-between px-5 md:h-22 md:px-[5vw]">
      <Link to="/" aria-label={tCommon('homeLink')} className="flex min-h-11 items-center no-underline">
        <Logo light />
      </Link>
      <nav aria-label={t('mainNav')} className="flex items-center gap-7 text-sm text-white">
        <a href="#voyages" className="hidden text-white no-underline md:inline">
          {t('inspirations')}
        </a>
        <a href="#methode" className="hidden text-white no-underline md:inline">
          {t('ourMethod')}
        </a>
        <Button asChild variant="glass">
          {signedIn ? <Link to="/wish">{t('mySpace')}</Link> : <Link to="/login">{t('signIn')}</Link>}
        </Button>
      </nav>
    </header>
  )
}
