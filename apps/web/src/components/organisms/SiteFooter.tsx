import { Link } from '@tanstack/react-router'

import { Logo } from '../atoms/Logo'

const YEAR = new Date().getFullYear()

/** The footer of the public pages. */
export function SiteFooter() {
  return (
    <footer className="grid items-center gap-8 bg-paper px-6 py-14 md:grid-cols-[1fr_1fr_1.4fr_auto] md:px-[5vw] md:pt-18 md:pb-9">
      <Link to="/" aria-label="Novoya, accueil" className="flex min-h-11 items-center no-underline">
        <Logo />
      </Link>
      <p className="m-0 font-serif text-base">Le voyage sur-mesure, avec l’intelligence de l’humain.</p>
      <p className="m-0 text-sm text-muted">Confidentialité · Mentions légales</p>
      <span className="text-xs text-muted">© {YEAR} Novoya</span>
    </footer>
  )
}
