import { useTranslation } from 'react-i18next'

import { formatDay, formatDayRange, formatEuros } from '@/lib/format'

import { Logo } from '../atoms/Logo'

type Props = {
  validDays: number
  /** ISO date. */
  issuedAt: string
  startDate: string
  endDate: string
  travellers: number
  days: number
  nights: number
  /** Amounts in whole euros. */
  lines: { label: string; amount: number }[]
  total: number
  budget: number
}

/** The agency's offer, laid out like a printed quote. Prices come from the agent, never the AI. */
export function QuoteSheet({ validDays, issuedAt, startDate, endDate, travellers, days, nights, lines, total, budget }: Props) {
  const { t, i18n } = useTranslation('quote')
  const locale = i18n.language
  return (
    <section aria-label={t('sheet.label')} className="my-9 bg-white px-4.5 py-6 shadow-card md:my-0 md:p-11">
      <div className="flex justify-between gap-4">
        <div className="grid">
          <Logo />
          <small className="mt-1 text-xs text-muted">{t('sheet.agency')}</small>
        </div>
        <div className="grid text-right text-xs">
          <b>{t('sheet.validity', { count: validDays })}</b>
          <span className="mt-1.5 text-muted">{t('sheet.issued', { date: formatDay(locale, issuedAt) })}</span>
        </div>
      </div>
      <ul className="my-8 flex flex-col gap-2 border-y border-line py-5 text-xs md:flex-row md:justify-between">
        <li>{formatDayRange(locale, startDate, endDate)}</li>
        <li>{t('sheet.travellers', { count: travellers })}</li>
        <li>
          {t('sheet.length', {
            days: t('sheet.days', { count: days }),
            nights: t('sheet.nights', { count: nights }),
          })}
        </li>
      </ul>
      <dl>
        {lines.map((line) => (
          <div key={line.label} className="flex justify-between border-b border-line py-4 text-sm">
            <dt>{line.label}</dt>
            <dd className="m-0 font-semibold">{formatEuros(locale, line.amount)}</dd>
          </div>
        ))}
        <div className="flex justify-between py-7 font-serif text-[25px]">
          <dt>{t('sheet.total')}</dt>
          <dd className="m-0">{formatEuros(locale, total)}</dd>
        </div>
      </dl>
      <p className="m-0 bg-ivory p-3 text-center text-xs">
        {t('sheet.budget', { amount: formatEuros(locale, budget) })}
      </p>
      <p className="mt-4 text-center text-xs text-muted">
        <button type="button" disabled className="min-h-11 underline underline-offset-4 disabled:cursor-not-allowed">
          {t('sheet.download')}
        </button>
        <br />
        {/* Disabled until the PDF exists (#52). */}
        {t('sheet.pdfSoon')}
      </p>
    </section>
  )
}
