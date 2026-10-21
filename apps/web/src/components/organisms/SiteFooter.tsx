import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Logo } from '../atoms/Logo'
import { LanguageChoice } from './LanguageChoice'

const YEAR = new Date().getFullYear()

/** The footer of the public pages. */
export function SiteFooter() {
  const { t } = useTranslation()
  return (
    <footer className="grid items-center gap-8 bg-paper px-6 py-14 md:grid-cols-[1fr_1fr_auto_1.4fr_auto] md:px-[5vw] md:pt-18 md:pb-9">
      <Link to="/" aria-label={t('homeLink')} className="flex min-h-11 items-center no-underline">
        <Logo />
      </Link>
      <p className="m-0 font-serif text-base">{t('footer.tagline')}</p>
      <Link to="/destinations" className="flex min-h-11 items-center text-sm text-ink underline underline-offset-4">
        {t('footer.destinations')}
      </Link>
      <p className="m-0 text-sm text-muted">{t('footer.legal')}</p>
      <div className="flex flex-wrap items-center gap-x-4">
        <LanguageChoice />
        <span className="text-xs text-muted">{t('footer.copyright', { year: YEAR })}</span>
      </div>
    </footer>
  )
}
