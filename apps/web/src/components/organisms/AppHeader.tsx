import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Button } from '../atoms/Button'

type Props = {
  /** The signed-in user's name. Without it, the header shows only the brand. */
  userName?: string
  onSignOut?: () => void
  signingOut?: boolean
  /** Shown when signing out failed: the user is still signed in. */
  signOutError?: string
}

export function AppHeader({ userName, onSignOut, signingOut = false, signOutError }: Props) {
  const { t } = useTranslation('header')
  return (
    <header className="app-header">
      <Link to="/" className="brand">
        Novoya
      </Link>
      {userName && (
        <div className="app-header__account">
          <span className="app-header__user">{userName}</span>
          <Button variant="quiet" onClick={onSignOut} disabled={signingOut}>
            {signingOut ? t('signingOut') : t('signOut')}
          </Button>
        </div>
      )}
      {signOutError && (
        <p role="alert" className="app-header__error">
          {signOutError}
        </p>
      )}
    </header>
  )
}
