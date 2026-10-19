import { createFileRoute } from '@tanstack/react-router'

import { AppShell } from '../../components/templates/AppShell'

export const Route = createFileRoute('/_authenticated/agent')({
  component: Page,
})

// Placeholder: the screen from the Figma mockup lands in the next pull request.
function Page() {
  return (
    <AppShell>
      <main className="px-5 py-16 md:px-[8vw]">
        <h1 className="text-5xl">Bientôt</h1>
      </main>
    </AppShell>
  )
}
