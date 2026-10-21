// Demo dates count from the day the app runs, so the demo trips always look upcoming (ADR 0003: no past trips).
import { localIsoDate } from '../lib/dates'

/** The day `days` days after `today` (before it when negative), as YYYY-MM-DD. */
export function daysFromToday(days: number, today = new Date()): string {
  return localIsoDate(new Date(today.getFullYear(), today.getMonth(), today.getDate() + days))
}

/** The first day of the month `months` months after this one, as YYYY-MM-DD. */
export function monthFromToday(months: number, today = new Date()): string {
  return localIsoDate(new Date(today.getFullYear(), today.getMonth() + months, 1))
}
