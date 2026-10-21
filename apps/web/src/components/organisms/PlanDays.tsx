import { Link } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import type { PlanItemResponse } from '../../api/generated/types.gen'
import { groupByDay } from '../../domain/plan/days'

import { Chip } from '../atoms/Chip'

/**
 * The plan's offers, day by day, on a vertical line. Never a price, never a partner (#31):
 * each offer opens its own page, where its indicative price is (ADR 0013).
 */
export function PlanDays({ items }: { items: PlanItemResponse[] }) {
  const { t } = useTranslation('plan')
  return (
    <section aria-label={t('daysLabel')} className="relative px-5 py-14 md:px-[14vw] md:py-22">
      <div aria-hidden="true" className="absolute top-14 bottom-24 left-[44px] w-px bg-line md:top-22 md:left-[calc(14vw+24px)]" />
      <ol>
        {groupByDay(items).map(({ day, items: dayItems }) => (
          <li key={day} className="relative grid grid-cols-[60px_1fr] md:grid-cols-[80px_1fr]">
            <div>
              <span
                aria-hidden="true"
                className="relative grid size-[49px] place-items-center rounded-full border border-ink bg-paper font-serif text-sm"
              >
                {String(day).padStart(2, '0')}
              </span>
            </div>
            <article className="min-w-0 border-t border-line pt-5.5 pb-16">
              <h2 className="mb-6 text-[34px] leading-tight">{t('live.day', { number: day })}</h2>
              <ul className="grid gap-6 md:grid-cols-2 md:gap-10">
                {dayItems.map((item) => (
                  <li key={item.id}>
                    {item.available ? (
                      <>
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          {item.kind && <Chip>{t(`live.kind.${item.kind}`)}</Chip>}
                          {item.quantity > 1 && <Chip>{t('live.quantity', { count: item.quantity })}</Chip>}
                        </div>
                        <h3 className="mb-2 font-serif text-lg tracking-normal">
                          <Link
                            to="/offers/$offerId"
                            params={{ offerId: item.offer_id }}
                            className="text-ink underline decoration-line underline-offset-4 hover:decoration-ink"
                          >
                            {item.title}
                          </Link>
                        </h3>
                        {item.description && <p className="m-0 text-sm leading-relaxed text-muted">{item.description}</p>}
                      </>
                    ) : (
                      <p className="m-0 text-sm text-muted italic">{t('live.unavailable')}</p>
                    )}
                    {item.note && <p className="mt-2 text-sm leading-relaxed">{item.note}</p>}
                  </li>
                ))}
              </ul>
            </article>
          </li>
        ))}
      </ol>
    </section>
  )
}
