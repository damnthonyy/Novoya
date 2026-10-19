/** What the client typed in the panel's last step, as the form holds it. */
export type ConstraintsInput = {
  budget: string
  persons: number
  startDate: string
  endDate: string
}

export type ConstraintsErrors = Partial<Record<keyof ConstraintsInput, string>>

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
  if (parseBudget(input.budget) === null) errors.budget = 'Indiquez un budget en euros, par exemple 3 500.'
  if (!Number.isInteger(input.persons) || input.persons < MIN_PERSONS || input.persons > MAX_PERSONS) {
    errors.persons = `Entre ${MIN_PERSONS} et ${MAX_PERSONS} voyageurs.`
  }
  if (!input.startDate) errors.startDate = 'Choisissez une date de départ.'
  if (!input.endDate) errors.endDate = 'Choisissez une date de retour.'
  else if (input.startDate && input.endDate <= input.startDate) {
    errors.endDate = 'Le retour doit être après le départ.'
  }
  return errors
}

/** "2 voyageurs", "1 voyageur". */
export function personsLabel(persons: number): string {
  return `${persons} voyageur${persons > 1 ? 's' : ''}`
}
