import { Chip } from '../atoms/Chip'
import { Eyebrow } from '../atoms/Eyebrow'

type Props = {
  version: number
  updatedLabel: string
  place: string
  tagline: string
  dates: string
  travellers: string
  tags: string[]
}

/** The top of a plan: its version, title and summary. Never a price (#31). */
export function PlanHeader({ version, updatedLabel, place, tagline, dates, travellers, tags }: Props) {
  return (
    <section className="bg-ivory px-5 pt-16 pb-10 md:flex md:items-end md:justify-between md:px-[8vw] md:pt-25 md:pb-20">
      <div>
        <div className="flex flex-wrap items-center gap-x-4">
          <Eyebrow>Votre aperçu · version {version}</Eyebrow>
          <span className="mb-6 text-xs text-muted">{updatedLabel}</span>
        </div>
        <h1 className="m-0 text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
          {place}{' '}
          <br />
          <em>{tagline}</em>
        </h1>
      </div>
      <div className="mt-9 md:mt-0 md:text-right">
        <p className="m-1.5 font-serif text-lg">{dates}</p>
        <p className="m-1.5 font-serif text-lg">{travellers}</p>
        <ul aria-label="Vos envies" className="mt-5 flex flex-wrap gap-1.5 md:justify-end">
          {tags.map((tag) => (
            <li key={tag}>
              <Chip>{tag}</Chip>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
