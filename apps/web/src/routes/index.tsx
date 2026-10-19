import { useQuery } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { getMeOptions } from '../api/generated/@tanstack/react-query.gen'
import { Button } from '../components/atoms/Button'
import { PublicHeader } from '../components/organisms/PublicHeader'
import { SiteFooter } from '../components/organisms/SiteFooter'

export const Route = createFileRoute('/')({
  component: LandingPage,
})

// Placeholder: the full landing page from the Figma mockup lands in the next pull request.
function LandingPage() {
  const me = useQuery({ ...getMeOptions(), retry: false })
  const { t } = useTranslation('home')
  return (
    <>
      <main className="relative min-h-[700px] bg-ink text-white">
        <PublicHeader signedIn={me.isSuccess} />
        <div className="px-6 pt-48 md:px-[8.3vw]">
          <h1 className="mb-8 text-6xl leading-[0.91] md:text-8xl">
            {t('titleStart')}
            <br />
            <em>{t('titleEnd')}</em>
          </h1>
          <Button asChild variant="coral" size="lg">
            <Link to="/wish">{t('describeTrip')}</Link>
          </Button>
        </div>
      </main>
      <SiteFooter />
    </>
  )
}
