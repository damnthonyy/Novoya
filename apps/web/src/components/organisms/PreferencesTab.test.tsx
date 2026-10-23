import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../../api/client'
import { client } from '../../api/generated/client.gen'
import type { PreferenceSectionOut } from '../../api/generated/types.gen'
import { sectionTones } from '../../domain/panel/sectionTone'
import i18n from '../../i18n'
import { TagGroup } from '../molecules/TagGroup'
import { PreferencesTab } from './PreferencesTab'

const SECTIONS: PreferenceSectionOut[] = [
  {
    id: 'style',
    title: 'Style',
    tags: [
      { id: 'beach', label: 'Beach', removable: true },
      { id: 'city', label: 'City', removable: true },
    ],
  },
  { id: 'food', title: 'Food', tags: [{ id: 'wine', label: 'Wine', removable: false }] },
]

let stored: PreferenceSectionOut[]
let calls: { method: string; path: string }[]

beforeEach(() => {
  client.setConfig({ baseUrl: 'http://api.test' })
  stored = structuredClone(SECTIONS)
  calls = []
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const path = new URL(request.url).pathname
    calls.push({ method: request.method, path })
    if (request.method === 'DELETE') {
      const [, , , section, tag] = path.split('/')
      stored = stored
        .map((s) => (s.id === section ? { ...s, tags: s.tags.filter((t) => t.id !== tag) } : s))
        .filter((s) => s.tags.length > 0)
      return new Response(null, { status: 204 })
    }
    return Response.json(stored)
  })
})

afterEach(() => vi.restoreAllMocks())

function renderTab() {
  const rootRoute = createRootRoute()
  const index = createRoute({ getParentRoute: () => rootRoute, path: '/', component: PreferencesTab })
  const wish = createRoute({ getParentRoute: () => rootRoute, path: '/wish', component: () => <p>wish page</p> })
  const router = createRouter({
    routeTree: rootRoute.addChildren([index, wish]),
    history: createMemoryHistory({ initialEntries: ['/'] }),
  })
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('PreferencesTab', () => {
  it('groups the preferences by section, each with its colour', async () => {
    renderTab()

    const style = await screen.findByRole('region', { name: 'Style' })
    const food = screen.getByRole('region', { name: 'Food' })
    expect(within(style).getByText('Beach')).toBeInTheDocument()
    expect(within(style).getByText('City')).toBeInTheDocument()
    expect(within(food).getByText('Wine')).toBeInTheDocument()
    const tones = sectionTones(['style', 'food'])
    expect(style).toHaveAttribute('data-tone', String(tones.get('style')))
    expect(food).toHaveAttribute('data-tone', String(tones.get('food')))
    expect(tones.get('style')).not.toBe(tones.get('food'))
  })

  it('removes a preference through the API and shows the change', async () => {
    renderTab()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove Beach' }))

    await waitFor(() => expect(screen.queryByText('Beach')).not.toBeInTheDocument())
    expect(calls).toContainEqual({ method: 'DELETE', path: '/me/preferences/style/beach' })
    expect(screen.getByText('City')).toBeInTheDocument()
  })

  it('shows a preference sent to the agency without a remove button', async () => {
    renderTab()

    const food = await screen.findByRole('region', { name: 'Food' })
    expect(within(food).getByText('Wine')).toBeInTheDocument()
    expect(within(food).getByText('Part of a trip sent to the agency')).toBeInTheDocument()
    expect(within(food).queryByRole('button')).not.toBeInTheDocument()
  })

  it('explains where preferences come from when there are none, with a link to the wish page', async () => {
    stored = []
    renderTab()

    expect(await screen.findByText(/come from the preference panel/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('link', { name: 'Describe a trip' }))
    expect(await screen.findByText('wish page')).toBeInTheDocument()
  })

  it('is translated in French', async () => {
    await i18n.changeLanguage('fr')
    renderTab()

    expect(await screen.findByRole('button', { name: 'Retirer Beach' })).toBeInTheDocument()
    expect(screen.getByText('Fait partie d’un voyage envoyé à l’agence')).toBeInTheDocument()
  })
})

describe('the preference panel', () => {
  it('uses the same colour for a section as the preferences tab', () => {
    const tone = sectionTones(['style', 'food']).get('food')
    render(<TagGroup title="Food" multi tags={[{ id: 'wine', label: 'Wine' }]} selected={[]} onToggle={() => {}} tone={tone} />)

    expect(screen.getByRole('group', { name: 'Food' })).toHaveAttribute('data-tone', String(tone))
  })
})

describe('sectionTones', () => {
  it('gives the usual sections fixed, different colours', () => {
    const tones = sectionTones(['style', 'rhythm', 'food', 'stay', 'activities'])
    expect(new Set(tones.values()).size).toBe(5)
    expect(sectionTones(['activities']).get('activities')).toBe(tones.get('activities'))
  })

  it('gives other sections the colours not used on the page first', () => {
    const tones = sectionTones(['activities', 'culture', 'nightlife', 'style', 'food'])
    expect(new Set(tones.values()).size).toBe(5)
  })

  it('gives the same colours for the same sections every time', () => {
    const ids = ['culture', 'style', 'nightlife']
    expect([...sectionTones(ids)]).toEqual([...sectionTones(ids)])
  })

  it('does not trip over section names that are object properties', () => {
    const tones = sectionTones(['constructor', '__proto__', 'toString'])
    expect([...tones.values()].every((tone) => tone >= 1 && tone <= 6)).toBe(true)
  })
})
