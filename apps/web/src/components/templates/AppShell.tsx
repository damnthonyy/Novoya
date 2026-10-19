import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

/**
 * The frame of a signed-in page: room for the fixed header, then the page.
 * `tone` is the page's background.
 */
export function AppShell({
  children,
  tone = 'paper',
  className,
}: {
  children: ReactNode
  tone?: 'paper' | 'ivory'
  className?: string
}) {
  return (
    <div className={cn('min-h-screen pt-18 md:pt-22', tone === 'ivory' ? 'bg-ivory' : 'bg-paper', className)}>
      {children}
    </div>
  )
}
