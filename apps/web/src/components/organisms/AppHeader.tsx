import { Link } from '@tanstack/react-router'

import { Avatar } from '../atoms/Avatar'
import { Logo } from '../atoms/Logo'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'

export type Role = 'client' | 'agent' | 'admin'

type Props = {
  /** The signed-in user's name. Without it, the header shows only the brand. */
  userName?: string
  role?: Role
  onSignOut?: () => void
  signingOut?: boolean
  /** Shown when signing out failed: the user is still signed in. */
  signOutError?: string
}

const navLink =
  'relative py-2 text-sm text-ink no-underline after:absolute after:inset-x-0 after:-bottom-[25px] after:h-0.5 data-[status=active]:after:bg-coral'

/** The header of every signed-in page: brand, main links and the account menu. */
export function AppHeader({ userName, role = 'client', onSignOut, signingOut = false, signOutError }: Props) {
  return (
    <header className="fixed inset-x-0 top-0 z-20 border-b border-line bg-paper/90 backdrop-blur-md">
      <div className="flex h-18 items-center justify-between px-5 md:h-22 md:px-[5vw]">
        <Link to="/" aria-label="Novoya, accueil" className="flex min-h-11 items-center no-underline">
          <Logo />
        </Link>
        {userName && (
          <>
            <nav aria-label="Navigation principale" className="hidden items-center gap-7 lg:flex">
              <Link to="/wish" className={navLink}>
                Composer
              </Link>
              <Link to="/trips" className={navLink}>
                Mes voyages
              </Link>
              {role !== 'client' && (
                <Link to="/agent" className={navLink}>
                  Espace agence
                </Link>
              )}
              {role === 'admin' && (
                <Link to="/admin" className={navLink}>
                  Administration
                </Link>
              )}
            </nav>
            <DropdownMenu>
              <DropdownMenuTrigger className="flex min-h-11 items-center gap-2.5 rounded-full text-sm">
                <Avatar name={userName} />
                <span className="hidden max-w-48 truncate lg:inline">{userName}</span>
                <span aria-hidden="true">⌄</span>
                <span className="sr-only lg:hidden">Menu du compte</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52 rounded-none border-0 p-2.5 shadow-menu">
                {/* Below lg the nav is hidden, so its links live here. */}
                <div className="lg:hidden">
                  <DropdownMenuItem asChild>
                    <Link to="/wish">Composer</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/trips">Mes voyages</Link>
                  </DropdownMenuItem>
                  {role !== 'client' && (
                    <DropdownMenuItem asChild>
                      <Link to="/agent">Espace agence</Link>
                    </DropdownMenuItem>
                  )}
                  {role === 'admin' && (
                    <DropdownMenuItem asChild>
                      <Link to="/admin">Administration</Link>
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                </div>
                <DropdownMenuItem disabled={signingOut} onSelect={onSignOut}>
                  {signingOut ? 'Déconnexion…' : 'Se déconnecter'}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        )}
      </div>
      {signOutError && (
        <p role="alert" className="bg-white px-5 py-2 text-right text-sm text-danger md:px-[5vw]">
          {signOutError}
        </p>
      )}
    </header>
  )
}
