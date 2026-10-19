import { useTranslation } from 'react-i18next'

import { formatDayRange, formatEuros, formatHoursAgo } from '@/lib/format'

import { Avatar } from '../atoms/Avatar'
import { Button } from '../atoms/Button'

type Props = {
  client: string
  title: string
  wish: string
  /** Whole euros. */
  budget: number
  startDate: string
  endDate: string
  travellers: number
  receivedHoursAgo: number
  onTake?: () => void
}

/** One quote request in the agency queue. */
export function RequestRow({ client, title, wish, budget, startDate, endDate, travellers, receivedHoursAgo, onTake }: Props) {
  const { t, i18n } = useTranslation('agent')
  const locale = i18n.language
  return (
    <article className="grid grid-cols-[40px_1fr] items-center gap-5 border-b border-line py-6 xl:grid-cols-[40px_1fr_160px_150px]">
      <Avatar name={client} />
      <div>
        <small className="text-xs text-muted">
          {t('request.meta', { received: formatHoursAgo(locale, receivedHoursAgo), client })}
        </small>
        <h2 className="my-2 font-serif text-xl tracking-normal">{title}</h2>
        <p className="m-0 text-sm text-muted">“{wish}”</p>
      </div>
      <dl className="col-start-2 grid xl:col-start-auto">
        <dt className="text-xs text-muted">{t('request.budgetMax')}</dt>
        <dd className="m-0 my-1 font-serif">{formatEuros(locale, budget)}</dd>
        <dd className="m-0 text-xs text-muted">
          {t('request.datesTravellers', { dates: formatDayRange(locale, startDate, endDate), count: travellers })}
        </dd>
      </dl>
      <Button className="col-start-2 justify-self-start xl:col-start-auto" onClick={onTake}>
        {t('request.take')}
      </Button>
    </article>
  )
}
