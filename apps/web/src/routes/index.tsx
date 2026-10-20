import { useQuery } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

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

// Three partner offers from the seed catalogue, shown as inspirations. Texts in home.json, trips.<id>.
const TRIPS = [
  { id: 'elounda', image: '/images/elounda-sea-view', tags: ['sea', 'calm', 'beach'] },
  { id: 'biarritz', image: '/images/biarritz-surf', tags: ['beach', 'sport', 'sea'] },
  { id: 'marrakech', image: '/images/marrakech-riad', tags: ['culture', 'calm', 'riad'] },
] as const

function LandingPage() {
  // Visitors are welcome: a 401 here only means "not signed in".
  const me = useQuery({ ...getMeOptions(), retry: false })
  const signedIn = me.isSuccess
  const { t } = useTranslation('home')

  return (
    <>
      <main>
        <LandingHero
          image="/images/crete-coast"
          imageAlt={t('heroImageAlt')}
          signedIn={signedIn}
          actions={
            <>
              <Button asChild variant="coral" size="lg">
                <Link to="/wish">
                  {t('describeTrip')} <span aria-hidden="true">↗</span>
                </Link>
              </Button>
              {!signedIn && (
                <Button asChild variant="glass" size="lg">
                  <a href={googleSignInUrl('/wish')}>
                    <span aria-hidden="true" className="font-[Arial] font-bold">
                      G
                    </span>
                    {t('continueWithGoogle')}
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
              key={trip.id}
              image={trip.image}
              imageAlt={t(`trips.${trip.id}.title`)}
              place={t(`trips.${trip.id}.place`)}
              title={t(`trips.${trip.id}.title`)}
              copy={t(`trips.${trip.id}.copy`)}
              tags={trip.tags.map((tag) => t(`tags.${tag}`))}
              badge={index === 0 ? t('popular.badgePopular') : t('popular.badgeSelection')}
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
          image="/images/elounda-sea-view"
          action={
            <Button asChild variant="coral" size="lg">
              <Link to="/wish">
                {t('closing.start')} <span aria-hidden="true">↗</span>
              </Link>
            </Button>
          }
        />
      </main>
      <SiteFooter />
    </>
  )
}
