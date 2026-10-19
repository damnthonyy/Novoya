import { Avatar } from '../atoms/Avatar'
import { Button } from '../atoms/Button'

type Props = {
  client: string
  title: string
  wish: string
  budget: string
  dates: string
  travellers: number
  received: string
  onTake?: () => void
}

/** One quote request in the agency queue. */
export function RequestRow({ client, title, wish, budget, dates, travellers, received, onTake }: Props) {
  return (
    <article className="grid grid-cols-[40px_1fr] items-center gap-5 border-b border-line py-6 xl:grid-cols-[40px_1fr_160px_150px]">
      <Avatar name={client} />
      <div>
        <small className="text-xs text-muted">
          {received} · Devis demandé · {client}
        </small>
        <h2 className="my-2 font-serif text-xl tracking-normal">{title}</h2>
        <p className="m-0 text-sm text-muted">“{wish}”</p>
      </div>
      <dl className="col-start-2 grid xl:col-start-auto">
        <dt className="text-xs text-muted">Budget max</dt>
        <dd className="m-0 my-1 font-serif">{budget}</dd>
        <dd className="m-0 text-xs text-muted">
          {dates} · {travellers} voy.
        </dd>
      </dl>
      <Button className="col-start-2 justify-self-start xl:col-start-auto" onClick={onTake}>
        Prendre le plan
      </Button>
    </article>
  )
}
