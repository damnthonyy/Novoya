import { Link } from '@tanstack/react-router'

import { Button } from '../atoms/Button'

type Props = {
  /** The signed-in user's name. Without it, the header shows only the brand. */
  userName?: string
  onSignOut?: () => void
  signingOut?: boolean
}

export function AppHeader({ userName, onSignOut, signingOut = false }: Props) {
  return (
    <header className="app-header">
      <Link to="/" className="brand">
        Novoya
      </Link>
      {userName && (
        <div className="app-header__account">
          <span className="app-header__user">{userName}</span>
          <Button variant="quiet" onClick={onSignOut} disabled={signingOut}>
            {signingOut ? 'Signing out…' : 'Sign out'}
          </Button>
        </div>
      )}
    </header>
  )
}
