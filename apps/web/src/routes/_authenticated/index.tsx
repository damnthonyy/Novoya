import { createFileRoute } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { ApiStatus } from '../../components/ApiStatus'
import { WishForm } from '../../components/WishForm'

export const Route = createFileRoute('/_authenticated/')({
  component: HomePage,
})

function HomePage() {
  const { t } = useTranslation('home')
  return (
    <section>
      <h1>{t('title')}</h1>
      <p>{t('intro')}</p>
      <WishForm  />
      <ApiStatus />
    </section>
  )
}
