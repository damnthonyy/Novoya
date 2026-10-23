import { useEffect, useState } from 'react'

type Props = {
  /** What is being done, in order. The last one stays until the parent removes the loader. */
  steps: readonly string[]
  /** How long each step shows before the next one. */
  everyMs: number
  /** `dark` for the ink background of the plan screen. */
  tone?: 'light' | 'dark'
  className?: string
}

/**
 * Timed steps shown while the model works (#166). The API does not report its progress: the
 * steps only tell the client the page is not stuck. The parent unmounts it as soon as the
 * answer arrives, whatever step it is on.
 */
export function WishProgress({ steps, everyMs, tone = 'light', className = '' }: Props) {
  const [current, setCurrent] = useState(0)
  const last = steps.length - 1

  // One timer per step, all set at the start: nothing runs after the last step.
  useEffect(() => {
    const timers = Array.from({ length: last }, (_, index) =>
      setTimeout(() => setCurrent(index + 1), (index + 1) * everyMs),
    )
    return () => timers.forEach(clearTimeout)
  }, [last, everyMs])

  const dark = tone === 'dark'
  return (
    <div className={`flex items-center gap-3 text-left ${className}`}>
      <span
        aria-hidden="true"
        className={`size-4 shrink-0 rounded-full border-2 border-t-transparent motion-safe:animate-spin ${
          dark ? 'border-coral' : 'border-ink'
        }`}
      />
      <div className="min-w-0">
        <p role="status" className={`text-sm ${dark ? 'text-white' : 'text-ink'}`}>
          {steps[current]}…
        </p>
        <ol aria-hidden="true" className="mt-1.5 flex gap-1.5">
          {steps.map((step, index) => (
            <li
              key={step}
              className={`h-1 w-6 rounded-full ${
                index <= current ? 'bg-coral' : dark ? 'bg-white/20' : 'bg-ink/15'
              }`}
            />
          ))}
        </ol>
      </div>
    </div>
  )
}
