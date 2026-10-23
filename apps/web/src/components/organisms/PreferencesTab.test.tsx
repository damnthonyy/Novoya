import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../../api/client'
import { client } from '../../api/generated/client.gen'
import type { PreferenceSectionOut } from '../../api/generated/types.gen'
import { sectionTone } from '../../domain/panel/sectionTone'
import i18n from '../../i18n'
import { TagGroup } from '../molecules/TagGroup'
import { PreferencesTab } from './PreferencesTab'

const SECTIONS: PreferenceSectionOut[] = [
  { id: 'style', title: 'Style', tags: [{ id: 'beach', label: 'Beach' }, { id: 'city', label: 'City' }] },
  { id: 'food', title: 'Food', tags: [{ id: 'wine', label: 'Wine' }] },
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
    expect(style).toHaveAttribute('data-tone', String(sectionTone('style')))
    expect(food).toHaveAttribute('data-tone', String(sectionTone('food')))
    expect(sectionTone('style')).not.toBe(sectionTone('food'))
  })

  it('removes a preference through the API and shows the change', async () => {
    renderTab()

    fireEvent.click(await screen.findByRole('button', { name: 'Remove Beach' }))

    await waitFor(() => expect(screen.queryByText('Beach')).not.toBeInTheDocument())
    expect(calls).toContainEqual({ method: 'DELETE', path: '/me/preferences/style/beach' })
    expect(screen.getByText('City')).toBeInTheDocument()
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
  })
})

describe('the preference panel', () => {
  it('uses the same colour for a section as the preferences tab', () => {
    render(<TagGroup title="Food" multi tags={[{ id: 'wine', label: 'Wine' }]} selected={[]} onToggle={() => {}} sectionId="food" />)

    expect(screen.getByRole('group', { name: 'Food' })).toHaveAttribute('data-tone', String(sectionTone('food')))
  })
})

describe('sectionTone', () => {
  it('gives the usual sections different colours, and the same colour every time', () => {
    const tones = ['style', 'rhythm', 'food', 'stay', 'activities'].map(sectionTone)
    expect(new Set(tones).size).toBe(tones.length)
    expect(sectionTone('something-new')).toBe(sectionTone('something-new'))
  })
})
