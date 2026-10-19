import { Link } from '@tanstack/react-router'

import { Button } from '../atoms/Button'
import { Logo } from '../atoms/Logo'

/** The header over the landing page's photo, for visitors. */
export function PublicHeader({ signedIn = false }: { signedIn?: boolean }) {
  return (
    <header className="absolute inset-x-0 top-0 z-10 flex h-18 items-center justify-between px-5 md:h-22 md:px-[5vw]">
      <Link to="/" aria-label="Novoya, accueil" className="flex min-h-11 items-center no-underline">
        <Logo light />
      </Link>
      <nav aria-label="Navigation principale" className="flex items-center gap-7 text-sm text-white">
        <a href="#voyages" className="hidden text-white no-underline md:inline">
          Inspirations
        </a>
        <a href="#methode" className="hidden text-white no-underline md:inline">
          Notre méthode
        </a>
        <Button asChild variant="glass">
          {signedIn ? <Link to="/wish">Mon espace</Link> : <Link to="/login">Se connecter</Link>}
        </Button>
      </nav>
    </header>
  )
}
