import { Logo } from '../atoms/Logo'

type Props = {
  validity: string
  issued: string
  dates: string
  travellers: string
  length: string
  lines: { label: string; amount: string }[]
  total: string
  budget: string
}

/** The agency's offer, laid out like a printed quote. Prices come from the agent, never the AI. */
export function QuoteSheet({ validity, issued, dates, travellers, length, lines, total, budget }: Props) {
  return (
    <section aria-label="Détail de l’offre" className="my-9 bg-white px-4.5 py-6 shadow-card md:my-0 md:p-11">
      <div className="flex justify-between gap-4">
        <div className="grid">
          <Logo />
          <small className="mt-1 text-xs text-muted">Agence de voyage</small>
        </div>
        <div className="grid text-right text-xs">
          <b>{validity}</b>
          <span className="mt-1.5 text-muted">{issued}</span>
        </div>
      </div>
      <ul className="my-8 flex flex-col gap-2 border-y border-line py-5 text-xs md:flex-row md:justify-between">
        <li>{dates}</li>
        <li>{travellers}</li>
        <li>{length}</li>
      </ul>
      <dl>
        {lines.map((line) => (
          <div key={line.label} className="flex justify-between border-b border-line py-4 text-sm">
            <dt>{line.label}</dt>
            <dd className="m-0 font-semibold">{line.amount}</dd>
          </div>
        ))}
        <div className="flex justify-between py-7 font-serif text-[25px]">
          <dt>Total TTC</dt>
          <dd className="m-0">{total}</dd>
        </div>
      </dl>
      <p className="m-0 bg-ivory p-3 text-center text-xs">Votre budget maximum communiqué : {budget}</p>
      <p className="mt-4 text-center text-xs text-muted">
        <button type="button" disabled className="min-h-11 underline underline-offset-4 disabled:cursor-not-allowed">
          ↓ Télécharger l’offre PDF
        </button>
        <br />
        Le PDF sera disponible avec l’envoi de l’offre (#52).
      </p>
    </section>
  )
}
