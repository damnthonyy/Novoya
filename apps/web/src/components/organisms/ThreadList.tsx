import { StatusPill } from '../atoms/StatusPill'
import { cn } from '@/lib/utils'

export type ThreadSummary = {
  id: string
  photo: string
  status: string
  highlight?: boolean
  place: string
  title: string
  version: string
  time: string
}

type Props = {
  threads: ThreadSummary[]
  selectedId: string
  onSelect: (id: string) => void
}

/** The client's trips, one card each. Choosing one shows its conversation. */
export function ThreadList({ threads, selectedId, onSelect }: Props) {
  return (
    <ul aria-label="Vos aperçus" className="flex flex-col gap-2">
      {threads.map((thread) => {
        const selected = thread.id === selectedId
        return (
          <li key={thread.id}>
            <button
              type="button"
              aria-current={selected ? 'true' : undefined}
              onClick={() => onSelect(thread.id)}
              className={cn(
                'grid w-full grid-cols-[75px_1fr] items-center gap-3.5 border border-line bg-white p-3 text-left sm:grid-cols-[100px_1fr_auto]',
                selected && 'border-ink shadow-[inset_3px_0_var(--color-coral)]',
              )}
            >
              <img src={thread.photo} alt="" className="block h-20 w-full object-cover sm:h-25" />
              <span className="grid justify-items-start">
                <StatusPill highlight={thread.highlight} className="mb-2">
                  {thread.status}
                </StatusPill>
                <small className="text-xs text-muted">{thread.place}</small>
                <b className="my-1 font-serif text-[17px] font-normal">{thread.title}</b>
                <span className="text-xs text-muted">{thread.version}</span>
              </span>
              <time className="hidden self-start text-xs text-muted sm:block">{thread.time}</time>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
