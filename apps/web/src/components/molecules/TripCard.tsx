import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

import { Chip } from '../atoms/Chip'

type Props = {
  image: string
  imageAlt: string
  /** The small label on the photo ("Populaire"). */
  badge: string
  place: string
  title: string
  copy: string
  tags: string[]
  /** The photo is taller for the first, featured card. */
  tall?: boolean
  /** The link around the card (a router `Link`), given the card's content. */
  renderLink: (content: ReactNode) => ReactNode
  className?: string
}

/** An inspiration: photo, place, title, a line and tags. The whole card is one link. */
export function TripCard({ image, imageAlt, badge, place, title, copy, tags, tall = false, renderLink, className }: Props) {
  return (
    <article className={cn('group', className)}>
      {renderLink(
        <>
          <div className={cn('relative h-[400px] overflow-hidden', tall ? 'md:h-[540px]' : 'md:h-[420px]')}>
            <img
              src={image}
              alt={imageAlt}
              loading="lazy"
              className="size-full object-cover transition-transform duration-700 group-hover:scale-[1.035]"
            />
            <span className="absolute top-4 left-4 rounded-full bg-paper px-3 py-2 text-xs tracking-[0.12em] uppercase">
              {badge}
            </span>
            <span
              aria-hidden="true"
              className="absolute right-4 bottom-4 grid size-[46px] place-items-center rounded-full bg-white text-lg transition group-hover:rotate-[5deg] group-hover:bg-coral"
            >
              ↗
            </span>
          </div>
          <div className="px-1 py-[22px]">
            <p className="mb-2.5 text-xs tracking-[0.16em] text-muted uppercase">{place}</p>
            <h3 className="mb-2 font-serif text-[25px] font-normal">{title}</h3>
            <p className="text-sm text-muted">{copy}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Chip key={tag}>{tag}</Chip>
              ))}
            </div>
          </div>
        </>,
      )}
    </article>
  )
}
