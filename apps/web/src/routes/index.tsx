import { useQuery } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'

import { googleSignInUrl } from '../api/auth'
import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'
import { Button } from '../components/atoms/Button'
import { TripCard } from '../components/molecules/TripCard'
import { LandingHero } from '../components/organisms/LandingHero'
import { Closing, Manifesto, Method, PopularTrips, Trust } from '../components/organisms/LandingSections'
import { SiteFooter } from '../components/organisms/SiteFooter'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

// Three partner offers from the seed catalogue, shown as inspirations.
const TRIPS = [
  {
    image: '/images/elounda-sea-view.jpg',
    place: 'Grèce · Chania',
    title: 'Chambre vue mer, Elounda',
    copy: 'Une semaine calme au bord de l’eau, petit-déjeuner inclus.',
    tags: ['mer', 'calme', 'plage'],
  },
  {
    image: '/images/biarritz-surf.jpg',
    place: 'France · Biarritz',
    title: 'Cours de surf, Grande Plage',
    copy: 'Une demi-journée face à l’Atlantique, planche incluse.',
    tags: ['plage', 'sport', 'mer'],
  },
  {
    image: '/images/marrakech-riad.jpg',
    place: 'Maroc · Marrakech',
    title: 'Chambre de riad dans la médina',
    copy: 'Une maison à cour confidentielle, séjour de 2 nuits minimum.',
    tags: ['culture', 'calme', 'riad'],
  },
]

function LandingPage() {
  // Visitors are welcome: a 401 here only means "not signed in".
  const me = useQuery({ ...getMeOptions(), retry: false })
  const signedIn = me.isSuccess

  return (
    <>
      <main>
        <LandingHero
          image="/images/crete-coast.jpg"
          imageAlt="Côte rocheuse de Crète baignée par une eau turquoise"
          signedIn={signedIn}
          actions={
            <>
              <Button asChild variant="coral" size="lg">
                <Link to="/wish">
                  Décrire mon voyage <span aria-hidden="true">↗</span>
                </Link>
              </Button>
              {!signedIn && (
                <Button asChild variant="glass" size="lg">
                  <a href={googleSignInUrl('/wish')}>
                    <span aria-hidden="true" className="font-[Arial] font-bold">
                      G
                    </span>
                    Continuer avec Google
                  </a>
                </Button>
              )}
            </>
          }
        />
        <Manifesto />
        <PopularTrips>
          {TRIPS.map((trip, index) => (
            <TripCard
              key={trip.title}
              {...trip}
              imageAlt={trip.title}
              badge={index === 0 ? 'Populaire' : 'Sélection'}
              tall={index === 0}
              renderLink={(content) => (
                <Link to="/wish" className="block text-ink no-underline">
                  {content}
                </Link>
              )}
            />
          ))}
        </PopularTrips>
        <Method />
        <Trust />
        <Closing
          image="/images/elounda-sea-view.jpg"
          action={
            <Button asChild variant="coral" size="lg">
              <Link to="/wish">
                Commencer <span aria-hidden="true">↗</span>
              </Link>
            </Button>
          }
        />
      </main>
      <SiteFooter />
    </>
  )
}
