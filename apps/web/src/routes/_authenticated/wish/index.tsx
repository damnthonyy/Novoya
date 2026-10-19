import { createFileRoute } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { WishForm } from '../../../components/WishForm'
import { AppShell } from '../../../components/templates/AppShell'

export const Route = createFileRoute('/_authenticated/wish/')({
  component: WishPage,
})

function WishPage() {
  const { t } = useTranslation('wish')
  return (
    <AppShell tone="ivory">
      <main className="px-5 py-16 md:px-[8vw]">
        <h1 className="text-5xl">{t('title')}</h1>
        <WishForm />
      </main>
    </AppShell>
  )
}
