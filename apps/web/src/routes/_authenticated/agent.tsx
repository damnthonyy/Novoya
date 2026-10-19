import { createFileRoute, redirect } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { Eyebrow } from '../../components/atoms/Eyebrow'
import { lineTabList, lineTabPanel, lineTabTrigger } from '../../components/molecules/lineTabs'
import { BackofficeLayout } from '../../components/organisms/BackofficeLayout'
import { RequestRow } from '../../components/organisms/RequestRow'
import { AppShell } from '../../components/templates/AppShell'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { DemoBanner } from '../../components/molecules/DemoBanner'
import { canOpen } from '../../domain/auth/roles'
import { listQuoteRequests, QUEUE_COUNTS, type QueueFilter } from '../../fixtures/agentQueue'

export const Route = createFileRoute('/_authenticated/agent')({
  beforeLoad: ({ context }) => {
    if (!canOpen(context.me.role, 'agent')) throw redirect({ to: '/wish' })
  },
  component: AgentPage,
})

const FILTERS: QueueFilter[] = ['unassigned', 'in_progress', 'decided']

// The queue is demo data until #51 exists: "Prendre le plan" does nothing yet.
function AgentPage() {
  const { t } = useTranslation('agent')
  return (
    <AppShell>
      <DemoBanner />
      <BackofficeLayout
        area={t('area')}
        items={[
          { label: t('nav.queue'), active: true, count: QUEUE_COUNTS.unassigned },
          { label: t('nav.files') },
          { label: t('nav.sent') },
          { label: t('nav.partners') },
        ]}
      >
        <div className="flex items-end justify-between">
          <div>
            <Eyebrow>{t('eyebrow')}</Eyebrow>
            <h1 className="m-0 text-[39px] md:text-[50px]">{t('title')}</h1>
          </div>
          <p className="m-0 flex items-center gap-2">
            <span className="font-serif text-[32px]">{QUEUE_COUNTS.unassigned}</span>
            <small className="text-muted">{t('toTake')}</small>
          </p>
        </div>
        <Tabs defaultValue="unassigned" className="mt-10">
          <TabsList className={`${lineTabList} gap-2.5`}>
            {FILTERS.map((filter) => (
              <TabsTrigger key={filter} value={filter} className={`${lineTabTrigger} px-3.5`}>
                {t('filterTab', { label: t(`filters.${filter}`), count: QUEUE_COUNTS[filter] })}
              </TabsTrigger>
            ))}
          </TabsList>
          {FILTERS.map((filter) => {
            const requests = listQuoteRequests(filter)
            return (
              <TabsContent key={filter} value={filter} className={lineTabPanel}>
                {requests.length === 0 ? (
                  <p className="py-8 text-muted">{t('emptySoon')}</p>
                ) : (
                  requests.map((request) => <RequestRow key={request.id} {...request} />)
                )}
              </TabsContent>
            )
          })}
        </Tabs>
      </BackofficeLayout>
    </AppShell>
  )
}
