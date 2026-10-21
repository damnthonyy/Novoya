import { describe, expect, it } from 'vitest'

import { localIsoDate } from '../lib/dates'
import { listQuoteRequests } from './agentQueue'
import { daysFromToday, monthFromToday } from './demoDates'
import { DEMO_PLAN_ID, getPlan } from './plans'
import { getQuote } from './quotes'
import { listThreads } from './trips'

describe('daysFromToday', () => {
  it('counts days from the given day, across months and years', () => {
    const today = new Date(2026, 11, 30, 23, 30)
    expect(daysFromToday(0, today)).toBe('2026-12-30')
    expect(daysFromToday(3, today)).toBe('2027-01-02')
    expect(daysFromToday(-1, today)).toBe('2026-12-29')
  })
})

describe('monthFromToday', () => {
  it('gives the first day of the month, n months later', () => {
    const today = new Date(2026, 10, 30)
    expect(monthFromToday(1, today)).toBe('2026-12-01')
    expect(monthFromToday(2, today)).toBe('2027-01-01')
  })
})

// The demo trips must look upcoming whatever the day the demo runs (ADR 0003: no past trips).
describe('demo fixtures', () => {
  const today = localIsoDate()
  const plan = getPlan(DEMO_PLAN_ID)!
  const quote = getQuote('NV-2026-0182')!
  const chania = listThreads().find((thread) => thread.id === 'chania')!

  it('start the Chania plan after today, its days in order from the start', () => {
    expect(plan.startDate > today).toBe(true)
    expect(plan.endDate > plan.startDate).toBe(true)
    plan.days.forEach((day, index) => expect(day.date).toBe(daysAfter(plan.startDate, index)))
  })

  it('give the Chania plan, quote, trip card and queue entry the same dates', () => {
    const request = listQuoteRequests('unassigned').find((entry) => entry.id === 'r1')!
    const range = { startDate: plan.startDate, endDate: plan.endDate }
    expect({ startDate: quote.startDate, endDate: quote.endDate }).toEqual(range)
    expect({ startDate: request.startDate, endDate: request.endDate }).toEqual(range)
    expect(chania.dates).toEqual({ start: plan.startDate, end: plan.endDate })
  })

  it('issue the quote before today, still valid', () => {
    expect(quote.issuedAt < today).toBe(true)
    expect(daysAfter(quote.issuedAt, quote.validDays) > today).toBe(true)
  })

  it('date every waiting request and every open trip after today', () => {
    for (const request of listQuoteRequests('unassigned')) expect(request.startDate > today).toBe(true)
    for (const thread of listThreads().filter((entry) => entry.status !== 'refused')) {
      if (thread.dates === null) continue
      const first = 'start' in thread.dates ? thread.dates.start : thread.dates.month
      expect(first > today, thread.id).toBe(true)
    }
  })
})

function daysAfter(iso: string, days: number): string {
  const [year, month, day] = iso.split('-').map(Number)
  return localIsoDate(new Date(year, month - 1, day + days))
}
