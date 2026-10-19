import { cn } from '@/lib/utils'

/** The Novoya wordmark. Wrap it in a link to the home page where it is clickable. */
export function Logo({ light = false, className }: { light?: boolean; className?: string }) {
  return (
    <span
      className={cn(
        'flex items-center gap-2.5 font-serif text-[25px] tracking-display',
        light ? 'text-white' : 'text-ink',
        className,
      )}
    >
      <span
        aria-hidden="true"
        className="grid size-[29px] place-items-center rounded-full border border-current text-base italic"
      >
        N
      </span>
      <span>novoya</span>
    </span>
  )
}
