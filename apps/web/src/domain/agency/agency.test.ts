import { describe, expect, it } from 'vitest'

import { agencyView, shown } from './agency'

describe('shown', () => {
  it('keeps a confirmed value', () => {
    expect(shown({ value: 'ok', status: 'confirmed' })).toBe('ok')
  })

  it('hides a value still to check', () => {
    expect(shown({ value: '02 40 00 00 00', status: 'to_check' })).toBeUndefined()
  })
})

describe('agencyView', () => {
  it('exposes confirmed identity and e-mail', () => {
    const agency = agencyView('fr')
    expect(agency.tradeName).toBe('DÉTOUR')
    expect(agency.displayName).toBe('DÉTOUR Voyages')
    expect(agency.foundedYear).toBe(2012)
    expect(agency.email).toBe('contact@detour-voyages.fr')
    expect(agency.logo.src).toBe('/images/logo')
    expect(agency.tagline).toBe('Voyages insolites et week-ends sur mesure')
  })

  it('hides phone, address, Atout France and social links until they are confirmed', () => {
    const agency = agencyView('fr')
    expect(agency.phone).toBeUndefined()
    expect(agency.address).toBeUndefined()
    expect(agency.social).toEqual([])
    expect(agency.legalLines.map((line) => line.key)).toEqual(['publisher', 'email'])
    expect(agency.legalLines.some((line) => line.value.includes('IM044'))).toBe(false)
    expect(agency.legalLines.some((line) => line.value.includes('Écluses'))).toBe(false)
  })

  it('hides English drafts of agency copy', () => {
    const agency = agencyView('en')
    expect(agency.tagline).toBeUndefined()
    expect(agency.descriptionShort).toBeUndefined()
  })
})
