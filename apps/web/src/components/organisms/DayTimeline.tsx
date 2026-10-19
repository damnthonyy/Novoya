import { Link } from '@tanstack/react-router'

import { Chip } from '../atoms/Chip'

export type DaySummary = {
  number: number
  label: string
  date: string
  title: string
  text: string
  mood: string
}

/** The plan's days on a vertical line, each one linking to its detail page. */
export function DayTimeline({ planId, days }: { planId: string; days: DaySummary[] }) {
  return (
    <section aria-label="Jour par jour" className="relative px-5 py-14 md:px-[14vw] md:py-22">
      <div aria-hidden="true" className="absolute top-14 bottom-24 left-[44px] w-px bg-line md:top-22 md:left-[calc(14vw+24px)]" />
      <ol>
        {days.map((day) => (
          <li key={day.number} className="relative grid grid-cols-[60px_1fr] md:grid-cols-[80px_1fr]">
            <div>
              <span
                aria-hidden="true"
                className="relative grid size-[49px] place-items-center rounded-full border border-ink bg-paper font-serif text-sm"
              >
                {String(day.number).padStart(2, '0')}
              </span>
            </div>
            <article className="grid gap-3.5 border-t border-line pt-5.5 pb-16 md:grid-cols-[1fr_1fr_190px] md:gap-10">
              <div>
                <p className="mb-3 text-xs tracking-[0.15em] text-muted uppercase">
                  {day.label} · {day.date}
                </p>
                <h2 className="mb-4 text-[34px] leading-tight">{day.title}</h2>
                <Chip>{day.mood}</Chip>
              </div>
              <p className="m-0 text-sm leading-relaxed text-muted">{day.text}</p>
              <Link
                to="/plans/$planId/days/$day"
                params={{ planId, day: String(day.number) }}
                className="flex min-h-11 items-center self-start text-sm text-ink underline underline-offset-4"
              >
                Découvrir cette journée <span aria-hidden="true">&nbsp;↗</span>
                <span className="sr-only"> : {day.title}</span>
              </Link>
            </article>
          </li>
        ))}
      </ol>
    </section>
  )
}
