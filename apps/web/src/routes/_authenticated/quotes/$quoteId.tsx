import { createFileRoute, notFound } from '@tanstack/react-router'

import { Eyebrow } from '../../../components/atoms/Eyebrow'
import { QuoteDecision } from '../../../components/organisms/QuoteDecision'
import { QuoteSheet } from '../../../components/organisms/QuoteSheet'
import { AppShell } from '../../../components/templates/AppShell'
import { getQuote } from '../../../fixtures/quotes'

export const Route = createFileRoute('/_authenticated/quotes/$quoteId')({
  loader: ({ params }) => {
    const quote = getQuote(params.quoteId)
    if (!quote) throw notFound()
    return quote
  },
  notFoundComponent: () => <p className="px-5 pt-32 md:px-[8vw]">Cette offre n’existe pas.</p>,
  component: QuotePage,
})

function QuotePage() {
  const quote = Route.useLoaderData()
  return (
    <AppShell tone="ivory">
      {/* The decision only shows a confirmation until the API exists (#54). */}
      <main className="px-5 py-14 md:grid md:grid-cols-[0.8fr_1.2fr_0.65fr] md:items-start md:gap-10 md:px-[7vw] md:py-20">
        <div className="md:sticky md:top-37">
          <Eyebrow>Offre de l’agence N° {quote.id}</Eyebrow>
          <h1 className="mb-6 text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
            Votre voyage
            <br />
            <em>{quote.place}</em>
          </h1>
          <p className="text-muted">Préparée avec soin par {quote.agentName}, votre conseillère Novoya.</p>
        </div>
        <QuoteSheet {...quote} />
        <QuoteDecision />
      </main>
    </AppShell>
  )
}
