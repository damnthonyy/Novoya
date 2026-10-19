/** What the client typed in the panel's last step, as the form holds it. */
export type ConstraintsInput = {
  budget: string
  persons: number
  startDate: string
  endDate: string
}

// Texts in errors.json under answers.<key>; the page passes { min, max } for answers.persons.
export type ConstraintsErrorKey =
  | 'answers.budget'
  | 'answers.persons'
  | 'answers.startDate'
  | 'answers.endDate'
  | 'answers.endBeforeStart'

export type ConstraintsErrors = Partial<Record<keyof ConstraintsInput, ConstraintsErrorKey>>

export const MIN_PERSONS = 1
export const MAX_PERSONS = 50 // AnswerPanelRequest.persons

/** "3 500 €", "3500,50" or "3500.5" as the decimal string the API takes ("3500.50"), or null. */
export function parseBudget(text: string): string | null {
  const cleaned = text.replace(/[\s  €]/g, '').replace(',', '.')
  if (!/^\d{1,8}(\.\d{1,2})?$/.test(cleaned)) return null
  const value = Number(cleaned)
  return value > 0 ? value.toFixed(2) : null
}

/** The API's rules for the answers: a budget above 0, 1 to 50 travellers, the return after the departure. */
export function constraintsErrors(input: ConstraintsInput): ConstraintsErrors {
  const errors: ConstraintsErrors = {}
  if (parseBudget(input.budget) === null) errors.budget = 'answers.budget'
  if (!Number.isInteger(input.persons) || input.persons < MIN_PERSONS || input.persons > MAX_PERSONS) {
    errors.persons = 'answers.persons'
  }
  if (!input.startDate) errors.startDate = 'answers.startDate'
  if (!input.endDate) errors.endDate = 'answers.endDate'
  else if (input.startDate && input.endDate <= input.startDate) {
    errors.endDate = 'answers.endBeforeStart'
  }
  return errors
}
