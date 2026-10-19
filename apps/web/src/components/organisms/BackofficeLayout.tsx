import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type Props = {
  /** The area's name, above the side links. */
  area: string
  items: { label: string; active?: boolean; count?: number }[]
  children: ReactNode
}

/** The agency and admin pages: a side list of sections (desktop) and the content. */
export function BackofficeLayout({ area, items, children }: Props) {
  return (
    <div className="min-h-[calc(100vh-88px)] md:grid md:grid-cols-[220px_1fr]">
      <aside aria-label={area} className="hidden flex-col gap-1 border-r border-line px-5.5 py-10 md:flex">
        <small className="mx-3 mb-5 text-xs tracking-[0.15em] text-muted uppercase">{area}</small>
        <ul>
          {items.map((item) => (
            <li
              key={item.label}
              aria-current={item.active ? 'page' : undefined}
              className={cn(
                'flex items-center justify-between rounded-[3px] p-3 text-sm',
                item.active ? 'bg-ivory font-semibold' : 'text-muted',
              )}
            >
              {item.label}
              {item.count !== undefined && <b className="rounded-full bg-coral px-1.5 text-xs">{item.count}</b>}
            </li>
          ))}
        </ul>
      </aside>
      <main className="px-5 py-11 md:px-[5vw] md:py-14">{children}</main>
    </div>
  )
}
