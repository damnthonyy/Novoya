import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../api/client'
import { client } from '../api/generated/client.gen'
import type { MeResponse, UserResponse } from '../api/generated/types.gen'
import { createAppRouter } from '../router'

const SUPER: MeResponse = {
  id: '00000000-0000-4000-8000-000000000001',
  email: 'arthur@novoya.fr',
  name: 'Arthur Roche',
  first_name: 'Arthur',
  last_name: 'Roche',
  role: 'super_admin',
  locale: 'en',
  status: 'active',
  email_verified: true,
  created_at: '2026-08-18T10:00:00Z',
  sign_in_methods: ['password'],
}

const row = (id: string, name: string, role: UserResponse['role']): UserResponse => ({
  id: `00000000-0000-4000-8000-00000000000${id}`,
  email: `${name.toLowerCase().split(' ')[0]}@novoya.fr`,
  name,
  first_name: name.split(' ')[0],
  last_name: name.split(' ')[1],
  role,
  locale: 'fr',
  status: 'active',
  status_changed_by: null,
  status_changed_at: null,
  email_verified: true,
  created_at: '2026-09-04T10:00:00Z',
})

const ME_ROW: UserResponse = { ...SUPER, status_changed_by: null, status_changed_at: null }
const OTHER_SUPER = row('2', 'Sami Haddad', 'super_admin')
const INES = row('3', 'Inès Faure', 'admin')
const LEA = row('4', 'Léa Morel', 'client')
const MARC = row('5', 'Marc Petit', 'agent')

let me: MeResponse
let users: UserResponse[]
// The code the API answers PATCH /admin/users/{id}/role with, or null to accept it.
let roleRefusal: string | null
let requests: { method: string; path: string; search: URLSearchParams; body?: unknown }[]

function mockApi() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const url = new URL(request.url)
    const body = request.method === 'GET' ? undefined : await request.clone().json().catch(() => undefined)
    requests.push({ method: request.method, path: url.pathname, search: url.searchParams, body })
    if (url.pathname === '/me') return Response.json(me)
    if (url.pathname === '/admin/users') {
      const role = url.searchParams.get('role')
      const q = url.searchParams.get('q')?.toLowerCase()
      return Response.json(
        users.filter(
          (user) =>
            (!role || user.role === role) &&
            (!q || user.email.includes(q) || (user.name ?? '').toLowerCase().includes(q)),
        ),
      )
    }
    const role = url.pathname.match(/^\/admin\/users\/([^/]+)\/role$/)
    if (role && request.method === 'PATCH') {
      if (roleRefusal) return Response.json({ code: roleRefusal, detail: 'refused' }, { status: 403 })
      const next = (body as { role: UserResponse['role'] }).role
      users = users.map((user) => (user.id === role[1] ? { ...user, role: next } : user))
      return Response.json(users.find((user) => user.id === role[1]))
    }
    return Response.json({ status: 'ok' })
  })
}

const patches = () => requests.filter((request) => request.method === 'PATCH')

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

const rowOf = (name: string) => screen.getByRole('row', { name: new RegExp(name) })

describe('admins page', () => {
  beforeEach(() => {
    client.setConfig({ baseUrl: 'http://api.test' })
    me = SUPER
    users = [ME_ROW, OTHER_SUPER, INES, LEA, MARC]
    roleRefusal = null
    requests = []
    mockApi()
  })
  afterEach(() => vi.restoreAllMocks())

  it('shows the Admins tab to a super admin only', async () => {
    renderAt('/admin')
    // The first render of the admin chunk can be slow on a cold start.
    expect(await screen.findByRole('link', { name: 'Admins' }, { timeout: 3000 })).toHaveAttribute('href', '/admin/admins')
  })

  it('hides the Admins tab from a plain admin', async () => {
    me = { ...SUPER, role: 'admin' }
    renderAt('/admin')
    await screen.findByRole('link', { name: 'Users' }, { timeout: 3000 })

    expect(screen.queryByRole('link', { name: 'Admins' })).not.toBeInTheDocument()
  })

  it('sends a plain admin who opens the URL back to the overview', async () => {
    me = { ...SUPER, role: 'admin' }
    const { router } = renderAt('/admin/admins')

    await waitFor(() => expect(router.state.location.pathname).toBe('/admin'), { timeout: 3000 })
    expect(screen.queryByRole('heading', { level: 1, name: 'Admins' })).not.toBeInTheDocument()
  })

  it('lists the admins and super admins, with the server commands', async () => {
    renderAt('/admin/admins')

    expect(await screen.findByRole('heading', { level: 1, name: 'Admins' }, { timeout: 3000 })).toBeInTheDocument()
    expect(await screen.findByRole('row', { name: /Inès Faure/ })).toBeInTheDocument()
    expect(rowOf('Sami Haddad')).toHaveTextContent('Super admin')
    expect(rowOf('Arthur Roche')).toBeInTheDocument()
    expect(screen.queryByRole('row', { name: /Léa Morel/ })).not.toBeInTheDocument()
    expect(
      screen.getByText('python -m novoya_api.accounts.presentation.cli grant-role --email <email> --role super_admin'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('python -m novoya_api.accounts.presentation.cli grant-role --email <email> --role admin'),
    ).toBeInTheDocument()
  })

  it('locks the super admin rows and the viewer own row', async () => {
    renderAt('/admin/admins')
    await screen.findByRole('row', { name: /Inès Faure/ }, { timeout: 3000 })

    expect(within(rowOf('Sami Haddad')).queryByRole('button')).not.toBeInTheDocument()
    expect(within(rowOf('Arthur Roche')).queryByRole('button')).not.toBeInTheDocument()
    expect(within(rowOf('Inès Faure')).getByRole('button', { name: /take back/i })).toBeInTheDocument()
  })

  it('takes the admin role back to agent by default, after a confirm', async () => {
    renderAt('/admin/admins')
    fireEvent.click(await screen.findByRole('button', { name: /take back.*Inès Faure/i }, { timeout: 3000 }))
    const dialog = await screen.findByRole('alertdialog')
    expect(within(dialog).getByRole('combobox')).toHaveValue('agent')
    expect(within(dialog).queryByRole('option', { name: 'Super admin' })).not.toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Change role' }))

    await waitFor(() =>
      expect(patches()).toEqual([
        expect.objectContaining({ path: `/admin/users/${INES.id}/role`, body: { role: 'agent' } }),
      ]),
    )
  })

  it('takes the admin role back to client when the super admin picks it', async () => {
    renderAt('/admin/admins')
    fireEvent.click(await screen.findByRole('button', { name: /take back.*Inès Faure/i }, { timeout: 3000 }))
    const dialog = await screen.findByRole('alertdialog')
    fireEvent.change(within(dialog).getByRole('combobox'), { target: { value: 'client' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Change role' }))

    await waitFor(() =>
      expect(patches()).toEqual([
        expect.objectContaining({ path: `/admin/users/${INES.id}/role`, body: { role: 'client' } }),
      ]),
    )
  })

  it('gives the admin role to a user found by name, after a confirm', async () => {
    renderAt('/admin/admins')
    fireEvent.change(await screen.findByLabelText('Find a user by email or name', {}, { timeout: 3000 }), {
      target: { value: 'marc' },
    })
    fireEvent.click(await screen.findByRole('button', { name: /give.*Marc Petit/i }))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('from Agent to Admin')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Change role' }))

    await waitFor(() =>
      expect(patches()).toEqual([
        expect.objectContaining({ path: `/admin/users/${MARC.id}/role`, body: { role: 'admin' } }),
      ]),
    )
  })

  it('sends nothing when the super admin cancels', async () => {
    renderAt('/admin/admins')
    fireEvent.click(await screen.findByRole('button', { name: /take back.*Inès Faure/i }, { timeout: 3000 }))
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Cancel' }))

    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument())
    expect(patches()).toEqual([])
  })

  it('says in plain words when the API refuses', async () => {
    roleRefusal = 'super_admin_server_only'
    renderAt('/admin/admins')
    fireEvent.click(await screen.findByRole('button', { name: /take back.*Inès Faure/i }, { timeout: 3000 }))
    fireEvent.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Change role' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This person is a super admin: their role and account are managed on the server only.',
    )
  })

  it('shows the page in French', async () => {
    me = { ...SUPER, locale: 'fr' }
    renderAt('/admin/admins')

    expect(await screen.findByRole('heading', { level: 1, name: 'Admins' }, { timeout: 3000 })).toBeInTheDocument()
    expect(await screen.findByText('Les super admins se gèrent uniquement sur le serveur')).toBeInTheDocument()
  })
})
