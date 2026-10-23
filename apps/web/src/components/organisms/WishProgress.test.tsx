import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { WishProgress } from './WishProgress'

const STEPS = ['Reading your wish', 'Finding destinations', 'Preparing your preferences']

beforeEach(() => {
  vi.useFakeTimers()
})
afterEach(() => {
  vi.useRealTimers()
})

describe('WishProgress', () => {
  it('announces the first step at once', () => {
    render(<WishProgress steps={STEPS} everyMs={3000} />)

    expect(screen.getByRole('status')).toHaveTextContent('Reading your wish')
  })

  it('moves to the next step as time goes', () => {
    render(<WishProgress steps={STEPS} everyMs={3000} />)

    act(() => vi.advanceTimersByTime(3000))
    expect(screen.getByRole('status')).toHaveTextContent('Finding destinations')

    act(() => vi.advanceTimersByTime(3000))
    expect(screen.getByRole('status')).toHaveTextContent('Preparing your preferences')
  })

  it('waits on the last step instead of starting over', () => {
    render(<WishProgress steps={STEPS} everyMs={3000} />)

    act(() => vi.advanceTimersByTime(60_000))

    expect(screen.getByRole('status')).toHaveTextContent('Preparing your preferences')
    expect(vi.getTimerCount()).toBe(0)
  })

  it('stops its timer when it goes away', () => {
    const { unmount } = render(<WishProgress steps={STEPS} everyMs={3000} />)

    unmount()

    expect(vi.getTimerCount()).toBe(0)
  })

  it('only animates when the device allows motion', () => {
    const { container } = render(<WishProgress steps={STEPS} everyMs={3000} />)

    const animated = [...container.querySelectorAll('[class*="animate-"]')]
    expect(animated.length).toBeGreaterThan(0)
    for (const element of animated) {
      for (const name of element.classList) {
        if (name.includes('animate-')) expect(name).toMatch(/^motion-safe:/)
      }
    }
  })
})
