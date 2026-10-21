import { cn } from '@/lib/utils'

const tones = {
  // Coral ring on a light background.
  coral: 'border border-coral text-coral-text',
  // Filled, for the concierge in conversations.
  ink: 'bg-ink text-white',
  // White ring on a dark background.
  light: 'border border-white/30 text-white',
}

/** DÉTOUR's round "D" mark, in several sizes. Decorative. */
export function Seal({
  tone = 'coral',
  className,
}: {
  tone?: keyof typeof tones
  className?: string
}) {
  return (
    <span
      aria-hidden="true"
      className={cn('grid size-8 shrink-0 place-items-center rounded-full font-serif italic', tones[tone], className)}
    >
      D
    </span>
  )
}
