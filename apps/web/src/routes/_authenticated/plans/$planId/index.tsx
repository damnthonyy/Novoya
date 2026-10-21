import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError, isUnauthenticated } from '../../../../api/errors'
import { getMeQueryKey, getPlanOptions } from '../../../../api/generated/@tanstack/react-query.gen'
import type { Plan } from '../../../../api/generated/types.gen'
import { Button } from '../../../../components/atoms/Button'
import { Eyebrow } from '../../../../components/atoms/Eyebrow'
import { DemoBanner } from '../../../../components/molecules/DemoBanner'
import { ErrorNote } from '../../../../components/molecules/ErrorNote'
import { ConversationDock } from '../../../../components/organisms/ConversationDock'
import { DayTimeline } from '../../../../components/organisms/DayTimeline'
import { PlanDays } from '../../../../components/organisms/PlanDays'
import { PlanHeader } from '../../../../components/organisms/PlanHeader'
import { AppShell } from '../../../../components/templates/AppShell'
import { DEMO_PLAN_ID, getPlan } from '../../../../fixtures/plans'
import { QuoteNote } from '../../../../components/molecules/QuoteNote'

export const Route = createFileRoute('/_authenticated/plans/$planId/')({
  component: PlanRoute,
})

// The demo plan stays for the demo trips (/trips); every other id is read from the API.
function PlanRoute() {
  const { planId } = Route.useParams()
  return planId === DEMO_PLAN_ID ? <DemoPlanPage /> : <PlanPage planId={planId} />
}

function NotFound() {
  const { t } = useTranslation('plan')
  return <p className="px-5 pt-32 md:px-[8vw]">{t('notFound')}</p>
}

/** The plan built from the client's answers, as GET /plans/{id} gives it. */
function PlanPage({ planId }: { planId: string }) {
  const { t } = useTranslation('plan')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const plan = useQuery({ ...getPlanOptions({ path: { plan_id: planId } }), retry: false })
  const signedOut = isUnauthenticated(plan.error)

  // The session ended while on the page: sign in again and come back here. The cached /me
  // goes first, or the sign-in page would see a session and send the client straight back.
  // The way back is built from the id, not the current location: that one turns into /login
  // while navigating, and would nest redirect after redirect.
  useEffect(() => {
    if (!signedOut) return
    queryClient.removeQueries({ queryKey: getMeQueryKey() })
    void navigate({ to: '/login', search: { redirect: `/plans/${encodeURIComponent(planId)}` }, replace: true })
  }, [signedOut, queryClient, navigate, planId])

  // 404: not the caller's plan, or no such plan. 403: not a client (an agent, an admin).
  // 422: the id is not even a plan id. Trying again would never change these.
  const missing = plan.error instanceof ApiError && [403, 404, 422].includes(plan.error.status)

  return (
    <AppShell>
      {/* Also while trying again after a failure: the click shows that something happens. */}
      {plan.isPending || signedOut || (plan.isError && plan.isFetching) ? (
        <p className="px-5 pt-32 text-muted md:px-[8vw]">{t('live.loading')}</p>
      ) : missing ? (
        <NotFound />
      ) : plan.isError ? (
        <ErrorNote message={t('live.loadFailed')} onRetry={() => plan.refetch()} />
      ) : (
        <LivePlan plan={plan.data} />
      )}
    </AppShell>
  )
}

function LivePlan({ plan }: { plan: Plan }) {
  const { t } = useTranslation('plan')
  return (
    <main>
      <section className="bg-ivory px-5 pt-16 pb-10 md:px-[8vw] md:pt-25 md:pb-20">
        <Eyebrow>{t('live.eyebrow')}</Eyebrow>
        <h1 className="m-0 text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
          {t('live.titleStart')}{' '}
          <br />
          <em>{t('live.titleEnd')}</em>
        </h1>
        <p className="mt-8 max-w-[660px] font-serif text-lg leading-relaxed">{plan.summary}</p>
        {!plan.based_on_preferences && <p className="mt-4 max-w-[660px] text-sm text-muted">{t('live.noPreferences')}</p>}
      </section>
      <PlanDays items={plan.items} />
      <QuoteNote />
      <QuoteCall />
    </main>
  )
}

function DemoPlanPage() {
  const plan = getPlan(DEMO_PLAN_ID)!
  return (
    <AppShell>
      <DemoBanner />
      <main className="lg:pb-24">
        <PlanHeader {...plan} />
        <DayTimeline planId={plan.id} days={plan.days} />
        <QuoteNote />
        <QuoteCall />
        <ConversationDock version={plan.version} />
      </main>
    </AppShell>
  )
}

function QuoteCall() {
  const { t } = useTranslation('plan')
  return (
    <section className="bg-ink px-6 py-15 text-white md:flex md:items-end md:justify-between md:px-[8vw] md:py-20">
      <div className="max-w-[660px]">
        <Eyebrow light>{t('cta.eyebrow')}</Eyebrow>
        <h2 className="mb-4 text-[43px] leading-tight md:text-[56px]">{t('cta.title')}</h2>
        <p className="leading-relaxed text-white/70">
          {t('cta.text')}
        </p>
      </div>
      {/* Asking for a quote is #50: until then the plan never leads to a price (#31). */}
      <div className="mt-6 grid gap-2 md:mt-0 md:justify-items-end">
        <Button variant="coral" size="lg" disabled className="w-full md:w-auto">
          {t('cta.button')}
        </Button>
        <small className="text-sm text-white/80">{t('cta.unavailable')}</small>
      </div>
    </section>
  )
}
