import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../api/client'
import { client } from '../api/generated/client.gen'
import type { MeResponse, UserResponse } from '../api/generated/types.gen'
import { createAppRouter } from '../router'

const ADMIN: MeResponse = {
  id: '00000000-0000-4000-8000-000000000001',
  email: 'arthur@novoya.fr',
  name: 'Arthur Roche',
  role: 'admin',
  locale: 'en',
  status: 'active',
  email_verified: true,
  created_at: '2026-08-18T10:00:00Z',
  sign_in_methods: ['password'],
}

const LEA: UserResponse = {
  id: '00000000-0000-4000-8000-000000000002',
  email: 'lea@novoya.fr',
  name: 'Léa Morel',
  role: 'client',
  locale: 'fr',
  status: 'active',
  email_verified: true,
  created_at: '2026-09-04T10:00:00Z',
}

let me: MeResponse
let users: UserResponse[]
let requests: { method: string; path: string; search: string; body?: unknown }[]

function mockApi() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const url = new URL(request.url)
    const body = request.method === 'GET' ? undefined : await request.clone().json().catch(() => undefined)
    requests.push({ method: request.method, path: url.pathname, search: url.search, body })
    if (url.pathname === '/me') return Response.json(me)
    if (url.pathname === '/admin/users') return Response.json(users)
    const role = url.pathname.match(/^\/admin\/users\/([^/]+)\/role$/)
    if (role && request.method === 'PATCH') {
      const next = (body as { role: UserResponse['role'] }).role
      users = users.map((user) => (user.id === role[1] ? { ...user, role: next } : user))
      return Response.json(users.find((user) => user.id === role[1]))
    }
    return Response.json({ status: 'ok' })
  })
}

function renderAt(url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const router = createAppRouter(queryClient, createMemoryHistory({ initialEntries: [url] }))
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { router }
}

describe('back-office and plan screens', () => {
  beforeEach(() => {
    client.setConfig({ baseUrl: 'http://api.test' })
    me = ADMIN
    users = [ADMIN, LEA]
    requests = []
    mockApi()
  })
  afterEach(() => vi.restoreAllMocks())

  it('lists the users for an admin', async () => {
    renderAt('/admin')

    const table = await screen.findByRole('table', { name: 'Users and roles' })
    expect(within(table).getByRole('rowheader', { name: /Léa Morel/ })).toBeInTheDocument()
    expect(within(table).getByRole('rowheader', { name: /Arthur Roche/ })).toBeInTheDocument()
  })

  it('changes a user role with PATCH /admin/users/{id}/role', async () => {
    renderAt('/admin')

    const select = await screen.findByRole('combobox', { name: 'Role of Léa Morel' })
    fireEvent.change(select, { target: { value: 'agent' } })

    await waitFor(() =>
      expect(requests).toContainEqual(
        expect.objectContaining({ method: 'PATCH', path: `/admin/users/${LEA.id}/role`, body: { role: 'agent' } }),
      ),
    )
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Role of Léa Morel' })).toHaveValue('agent'))
  })

  it('does not let an admin change their own role', async () => {
    renderAt('/admin')

    expect(await screen.findByRole('combobox', { name: 'Role of Arthur Roche' })).toBeDisabled()
  })

  it('filters the users by role', async () => {
    renderAt('/admin')

    fireEvent.change(await screen.findByRole('combobox', { name: 'Filter by role' }), { target: { value: 'agent' } })

    await waitFor(() =>
      expect(requests).toContainEqual(expect.objectContaining({ path: '/admin/users', search: expect.stringContaining('role=agent') })),
    )
  })

  it("shows the admin page in the admin's language", async () => {
    me = { ...ADMIN, locale: 'fr' }
    renderAt('/admin')

    expect(await screen.findByRole('heading', { level: 1, name: 'Utilisateurs' })).toBeInTheDocument()
    expect(await screen.findByRole('table', { name: 'Utilisateurs et rôles' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: 'Rôle de Léa Morel' })).toHaveDisplayValue('Client')
    expect(document.documentElement).toHaveAttribute('lang', 'fr')
  })

  it('formats the quote amounts in the interface language', async () => {
    renderAt('/quotes/NV-2026-0182')

    expect(await screen.findByText('€2,750')).toBeInTheDocument()
    expect(screen.getByText('7 days / 6 nights')).toBeInTheDocument()
  })

  it.each(['/agent', '/admin'])('sends a client away from %s', async (url) => {
    me = { ...ADMIN, role: 'client' }
    const { router } = renderAt(url)

    await waitFor(() => expect(router.state.location.pathname).toBe('/wish'))
  })

  it('opens the agency queue for an agent, but not the admin pages', async () => {
    me = { ...ADMIN, role: 'agent' }
    const { router } = renderAt('/agent')

    expect(await screen.findByRole('heading', { name: 'Quote requests' })).toBeInTheDocument()

    await router.navigate({ to: '/admin' })
    await waitFor(() => expect(router.state.location.pathname).toBe('/wish'))
  })

  it('shows a plan without any price', async () => {
    renderAt('/plans/chania')

    expect(await screen.findByRole('heading', { level: 1, name: 'Chania, au rythme de la mer.' })).toBeInTheDocument()
    expect(document.body.textContent).not.toContain('€')
  })

  it('opens a day of the plan', async () => {
    renderAt('/plans/chania/days/2')

    expect(await screen.findByRole('heading', { name: 'La côte au réveil.' })).toBeInTheDocument()
  })

  it('confirms when the client accepts the quote', async () => {
    renderAt('/quotes/NV-2026-0182')

    fireEvent.click(await screen.findByRole('button', { name: 'Accept the offer' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Your advisor is confirming the bookings')
  })

  it('shows the conversation of the chosen trip', async () => {
    renderAt('/trips')

    fireEvent.click(await screen.findByRole('button', { name: /Marrakech, derrière les portes/ }))

    expect(await screen.findByRole('region', { name: 'History: Marrakech, derrière les portes' })).toBeInTheDocument()
  })
})
