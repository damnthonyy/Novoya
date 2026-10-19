import { createFileRoute } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { AppShell } from '../../components/templates/AppShell'

export const Route = createFileRoute('/_authenticated/admin')({
  component: Page,
})

// Placeholder: the screen from the Figma mockup lands in the next pull request.
function Page() {
  const { t } = useTranslation()
  return (
    <AppShell>
      <main className="px-5 py-16 md:px-[8vw]">
        <h1 className="text-5xl">{t('comingSoon')}</h1>
      </main>
    </AppShell>
  )
}
