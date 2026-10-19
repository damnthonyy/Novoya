import { createFileRoute, redirect } from '@tanstack/react-router'

import { Eyebrow } from '../../components/atoms/Eyebrow'
import { lineTabList, lineTabPanel, lineTabTrigger } from '../../components/molecules/lineTabs'
import { BackofficeLayout } from '../../components/organisms/BackofficeLayout'
import { RequestRow } from '../../components/organisms/RequestRow'
import { AppShell } from '../../components/templates/AppShell'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { canOpen } from '../../domain/auth/roles'
import { listQuoteRequests, QUEUE_COUNTS, type QueueFilter } from '../../fixtures/agentQueue'

export const Route = createFileRoute('/_authenticated/agent')({
  beforeLoad: ({ context }) => {
    if (!canOpen(context.me.role, 'agent')) throw redirect({ to: '/wish' })
  },
  component: AgentPage,
})

const FILTERS: { value: QueueFilter; label: string }[] = [
  { value: 'unassigned', label: 'À assigner' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'decided', label: 'Décidés' },
]

// The queue is demo data until #51 exists: "Prendre le plan" does nothing yet.
function AgentPage() {
  return (
    <AppShell>
      <BackofficeLayout
        area="Espace agence"
        items={[
          { label: 'File des demandes', active: true, count: QUEUE_COUNTS.unassigned },
          { label: 'Mes dossiers' },
          { label: 'Devis envoyés' },
          { label: 'Partenaires & offres' },
        ]}
      >
        <div className="flex items-end justify-between">
          <div>
            <Eyebrow>File agence</Eyebrow>
            <h1 className="m-0 text-[39px] md:text-[50px]">Demandes de devis</h1>
          </div>
          <p className="m-0 flex items-center gap-2">
            <span className="font-serif text-[32px]">{QUEUE_COUNTS.unassigned}</span>
            <small className="text-muted">à prendre</small>
          </p>
        </div>
        <Tabs defaultValue="unassigned" className="mt-10">
          <TabsList className={`${lineTabList} gap-2.5`}>
            {FILTERS.map((filter) => (
              <TabsTrigger key={filter.value} value={filter.value} className={`${lineTabTrigger} px-3.5`}>
                {filter.label} · {QUEUE_COUNTS[filter.value]}
              </TabsTrigger>
            ))}
          </TabsList>
          {FILTERS.map((filter) => {
            const requests = listQuoteRequests(filter.value)
            return (
              <TabsContent key={filter.value} value={filter.value} className={lineTabPanel}>
                {requests.length === 0 ? (
                  <p className="py-8 text-muted">Bientôt : les dossiers de cet onglet.</p>
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
