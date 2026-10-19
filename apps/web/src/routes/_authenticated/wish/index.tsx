import { createFileRoute } from '@tanstack/react-router'

import { WishForm } from '../../../components/WishForm'
import { AppShell } from '../../../components/templates/AppShell'

export const Route = createFileRoute('/_authenticated/wish/')({
  component: WishPage,
})

function WishPage() {
  return (
    <AppShell tone="ivory">
      <main className="px-5 py-16 md:px-[8vw]">
        <h1 className="text-5xl">De quoi avez-vous envie ?</h1>
        <WishForm />
      </main>
    </AppShell>
  )
}
