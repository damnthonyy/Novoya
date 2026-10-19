import { createFileRoute, Link, notFound } from '@tanstack/react-router'

import { Button } from '../../../../components/atoms/Button'
import { Eyebrow } from '../../../../components/atoms/Eyebrow'
import { ConversationDock } from '../../../../components/organisms/ConversationDock'
import { DayTimeline } from '../../../../components/organisms/DayTimeline'
import { PlanHeader } from '../../../../components/organisms/PlanHeader'
import { AppShell } from '../../../../components/templates/AppShell'
import { getPlan } from '../../../../fixtures/plans'

export const Route = createFileRoute('/_authenticated/plans/$planId/')({
  loader: ({ params }) => {
    const plan = getPlan(params.planId)
    if (!plan) throw notFound()
    return plan
  },
  notFoundComponent: () => <p className="px-5 pt-32 md:px-[8vw]">Cet aperçu n’existe pas.</p>,
  component: PlanPage,
})

function PlanPage() {
  const plan = Route.useLoaderData()
  return (
    <AppShell>
      <main className="lg:pb-24">
        <PlanHeader {...plan} />
        <DayTimeline planId={plan.id} days={plan.days} />
        <section className="bg-ink px-6 py-15 text-white md:flex md:items-end md:justify-between md:px-[8vw] md:py-20">
          <div className="max-w-[660px]">
            <Eyebrow light>La conversation continue</Eyebrow>
            <h2 className="mb-4 text-[43px] leading-tight md:text-[56px]">Cet aperçu vous ressemble ?</h2>
            <p className="leading-relaxed text-white/70">
              Continuez à l’affiner avec le concierge, ou transmettez-le à un conseiller Novoya lorsqu’il vous convient.
            </p>
          </div>
          <Button asChild variant="coral" size="lg" className="mt-6 w-full md:mt-0 md:w-auto">
            <Link to="/quotes/$quoteId" params={{ quoteId: plan.quoteId }}>
              Demander un devis à un conseiller <span aria-hidden="true">↗</span>
            </Link>
          </Button>
        </section>
        <ConversationDock version={plan.version} />
      </main>
    </AppShell>
  )
}
