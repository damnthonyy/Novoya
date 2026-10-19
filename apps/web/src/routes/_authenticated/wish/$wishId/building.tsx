import { createFileRoute, Link } from '@tanstack/react-router'

import { Button } from '../../../../components/atoms/Button'
import { Eyebrow } from '../../../../components/atoms/Eyebrow'
import { AppShell } from '../../../../components/templates/AppShell'

export const Route = createFileRoute('/_authenticated/wish/$wishId/building')({
  component: BuildingPage,
})

// The plan is built from here once the plan API lands (#29, #78); until then this page does
// not wait for it and points to the client's trips instead.
function BuildingPage() {
  return (
    <AppShell className="bg-ink">
      <main className="flex min-h-[calc(100vh-72px)] flex-col items-center justify-center p-[30px] text-center text-white md:min-h-[calc(100vh-88px)]">
        <div className="relative mb-10 grid size-[150px] place-items-center rounded-full border border-white/15">
          <div aria-hidden="true" className="absolute size-[105px] animate-orbit rounded-full border-t border-coral" />
          <span aria-hidden="true" className="font-serif text-[38px] italic">
            N
          </span>
        </div>
        <Eyebrow light>Votre aperçu prend forme</Eyebrow>
        <h1 className="mb-[30px] text-[45px] leading-none md:text-[65px]">
          On cale les soirées
          <br />
          <em>au bon rythme…</em>
        </h1>
        <div
          role="progressbar"
          aria-label="Composition de l’aperçu"
          aria-valuetext="En cours"
          className="h-0.5 w-[min(330px,80vw)] overflow-hidden bg-white/15"
        >
          <span className="block h-full w-[70%] animate-grow bg-coral" />
        </div>
        <p role="status" className="mt-[18px] text-sm text-white/65">
          Nous parcourons uniquement les offres de nos partenaires actifs.
        </p>
        <Button asChild variant="link" size="inline" className="mt-4 min-h-11 text-white">
          <Link to="/trips">Voir mes voyages →</Link>
        </Button>
      </main>
    </AppShell>
  )
}
