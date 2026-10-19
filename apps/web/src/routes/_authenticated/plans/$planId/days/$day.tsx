import { createFileRoute, Link, notFound } from '@tanstack/react-router'

import { Eyebrow } from '../../../../../components/atoms/Eyebrow'
import { ConversationDock } from '../../../../../components/organisms/ConversationDock'
import { AppShell } from '../../../../../components/templates/AppShell'
import { getPlan } from '../../../../../fixtures/plans'

export const Route = createFileRoute('/_authenticated/plans/$planId/days/$day')({
  loader: ({ params }) => {
    const plan = getPlan(params.planId)
    const day = plan?.days.find((item) => String(item.number) === params.day)
    if (!plan || !day) throw notFound()
    return { plan, day }
  },
  notFoundComponent: () => <p className="px-5 pt-32 md:px-[8vw]">Cette journée n’existe pas.</p>,
  component: DayPage,
})

function DayPage() {
  const { plan, day } = Route.useLoaderData()
  // The title on two lines, the second in italics, as in the mockup.
  const words = day.title.split(' ')
  const cut = Math.max(1, Math.floor(words.length / 2))
  const first = words.slice(0, cut).join(' ')
  const rest = words.slice(cut)
  return (
    <AppShell>
      <main>
        <Link
          to="/plans/$planId"
          params={{ planId: plan.id }}
          className="mx-6 my-4 inline-flex min-h-11 items-center text-ink underline underline-offset-4 md:mx-[5vw] md:my-6"
        >
          ← Retour à l’aperçu
        </Link>
        <section className="flex flex-col-reverse md:grid md:min-h-[calc(100vh-150px)] md:grid-cols-2">
          <div className="px-6 pt-11 pb-10 md:px-[9vw] md:py-12 lg:pb-28">
            <Eyebrow>
              {day.label} · {day.date}
            </Eyebrow>
            <h1 className="text-[55px] leading-[0.95] md:text-[75px]">
              {first}{' '}
              <br />
              <em>{rest.join(' ')}.</em>
            </h1>
            <p className="font-serif text-[19px] leading-relaxed text-muted">{day.intro}</p>
            <ol className="mt-12">
              {day.moments.map((moment) => (
                <li key={moment.time} className="grid grid-cols-[55px_20px_1fr] gap-3">
                  <time className="text-xs">{moment.time}</time>
                  <span aria-hidden="true" className="mt-1.5 size-[7px] rounded-full bg-coral" />
                  <article className="border-l border-line pb-7.5 pl-6">
                    <small className="text-xs text-muted">{moment.period}</small>
                    <h2 className="my-1.5 font-serif text-lg tracking-normal">{moment.title}</h2>
                    <p className="text-sm text-muted">{moment.text}</p>
                  </article>
                </li>
              ))}
            </ol>
          </div>
          <img src={plan.photo} alt={plan.photoAlt} className="block h-[330px] w-full object-cover md:h-full" />
        </section>
        <ConversationDock version={plan.version} />
      </main>
    </AppShell>
  )
}
