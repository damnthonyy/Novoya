import { describe, expect, it } from 'vitest'

import { constraintsErrors, parseBudget } from './constraints'

describe('parseBudget', () => {
  it.each([
    ['3500', '3500.00'],
    ['3 500 €', '3500.00'],
    ['3 500', '3500.00'],
    ['3500,5', '3500.50'],
    ['3500.25', '3500.25'],
  ])('reads %j as %s', (text, expected) => {
    expect(parseBudget(text)).toBe(expected)
  })

  it.each(['', '0', '-20', 'abc', '12.345', '123456789'])('refuses %j', (text) => {
    expect(parseBudget(text)).toBeNull()
  })
})

describe('constraintsErrors', () => {
  const valid = { budget: '3 500', persons: 2, startDate: '2026-05-12', endDate: '2026-05-19' }

  it('accepts valid answers', () => {
    expect(constraintsErrors(valid)).toEqual({})
  })

  it('needs a budget, 1 to 50 travellers and both dates', () => {
    const errors = constraintsErrors({ budget: '', persons: 0, startDate: '', endDate: '' })
    expect(Object.keys(errors).sort()).toEqual(['budget', 'endDate', 'persons', 'startDate'])
    expect(constraintsErrors({ ...valid, persons: 51 }).persons).toBe('answers.persons')
  })

  it('needs the return after the departure', () => {
    expect(constraintsErrors({ ...valid, endDate: '2026-05-12' }).endDate).toBe('answers.endBeforeStart')
    expect(constraintsErrors({ ...valid, endDate: '2026-05-01' }).endDate).toBe('answers.endBeforeStart')
  })
})
