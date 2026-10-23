import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../api/client'
import { client } from '../api/generated/client.gen'
import type { MeResponse } from '../api/generated/types.gen'
import i18n from '../i18n'
import { createAppRouter } from '../router'

const CAMILLE: MeResponse = {
  id: '6f1c2b1e-0000-4000-8000-000000000003',
  email: 'camille@exemple.fr',
  name: 'Camille Durand',
  first_name: 'Camille',
  last_name: 'Durand',
  role: 'client',
  locale: 'en',
  status: 'active',
  email_verified: true,
  created_at: '2026-10-01T10:00:00Z',
  sign_in_methods: ['password'],
}

type Call = { method: string; path: string; body: unknown }

let me: MeResponse
let calls: Call[]
/** What PATCH /me answers. By default, the stored user with the body applied. */
let patchAnswer: ((body: Record<string, string>) => Response) | undefined

function mockApi() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const path = new URL(request.url).pathname
    const text = ['POST', 'PATCH'].includes(request.method) ? await request.text() : ''
    const body = text ? JSON.parse(text) : undefined
    calls.push({ method: request.method, path, body })
    if (path === '/me' && request.method === 'PATCH') {
      if (patchAnswer) return patchAnswer(body)
      me = { ...me, ...body, name: `${body.first_name ?? me.first_name} ${body.last_name ?? me.last_name}` }
      return Response.json(me)
    }
    if (path === '/me') return Response.json(me)
    if (path.startsWith('/plans') || path.startsWith('/wishes')) return Response.json([])
    return new Response(null, { status: 204 })
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

async function openProfileTab() {
  fireEvent.mouseDown(await screen.findByRole('tab', { name: 'Personal information' }))
  return screen.findByRole('form', { name: 'Personal information' })
}

const patches = () => calls.filter((call) => call.method === 'PATCH' && call.path === '/me')
const meReads = () => calls.filter((call) => call.method === 'GET' && call.path === '/me').length

beforeEach(async () => {
  client.setConfig({ baseUrl: 'http://api.test' })
  me = { ...CAMILLE }
  calls = []
  patchAnswer = undefined
  mockApi()
  await i18n.changeLanguage('en')
})
afterEach(async () => {
  vi.restoreAllMocks()
  localStorage.clear()
  await i18n.changeLanguage('en')
})

describe('the personal information tab on My trips', () => {
  it('shows the signed-in client from GET /me instead of "coming soon"', async () => {
    renderAt('/trips')
    const form = await openProfileTab()

    expect(within(form).getByLabelText('First name')).toHaveValue('Camille')
    expect(within(form).getByLabelText('Last name')).toHaveValue('Durand')
    expect(within(form).getByLabelText('E-mail')).toHaveValue('camille@exemple.fr')
    expect(within(form).getByLabelText('Language')).toHaveValue('en')
    expect(screen.queryByText(/Coming soon: your personal information/)).not.toBeInTheDocument()
  })

  it('shows the email but does not let it be changed', async () => {
    renderAt('/trips')
    const form = await openProfileTab()

    const email = within(form).getByLabelText('E-mail')
    expect(email).toHaveAttribute('readonly')
    expect(email).toHaveAccessibleDescription(/sign in/i)
  })

  it('saves the names and the language, says so, and shows the stored values', async () => {
    renderAt('/trips')
    const form = await openProfileTab()
    const readsBefore = meReads()

    fireEvent.change(within(form).getByLabelText('First name'), { target: { value: 'Camille-Anne' } })
    fireEvent.change(within(form).getByLabelText('Last name'), { target: { value: 'Martin' } })
    fireEvent.click(within(form).getByRole('button', { name: 'Save' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Your details are saved.')
    expect(patches()).toEqual([
      { method: 'PATCH', path: '/me', body: { first_name: 'Camille-Anne', last_name: 'Martin', locale: 'en' } },
    ])
    // /me is read again: everything that shows the user follows.
    await waitFor(() => expect(meReads()).toBeGreaterThan(readsBefore))
    expect(within(form).getByLabelText('First name')).toHaveValue('Camille-Anne')
    expect(within(form).getByLabelText('Last name')).toHaveValue('Martin')
  })

  it('shows the values the API stored, not only what was typed', async () => {
    patchAnswer = () => {
      me = { ...me, first_name: 'Camille', last_name: 'Martin', name: 'Camille Martin' }
      return Response.json(me)
    }
    renderAt('/trips')
    const form = await openProfileTab()

    fireEvent.change(within(form).getByLabelText('Last name'), { target: { value: '  Martin  ' } })
    fireEvent.click(within(form).getByRole('button', { name: 'Save' }))

    await screen.findByRole('status')
    expect(within(form).getByLabelText('Last name')).toHaveValue('Martin')
  })

  it('shows a name error next to its field', async () => {
    patchAnswer = () =>
      Response.json(
        { code: 'invalid_input', detail: 'first_name: String should have at least 1 character' },
        { status: 422 },
      )
    renderAt('/trips')
    const form = await openProfileTab()

    fireEvent.change(within(form).getByLabelText('First name'), { target: { value: ' ' } })
    fireEvent.click(within(form).getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(within(form).getByLabelText('First name')).toHaveAccessibleDescription('Enter your first name.'),
    )
    expect(within(form).getByLabelText('First name')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows another failure above the button', async () => {
    patchAnswer = () => Response.json({ code: 'boom', detail: 'boom' }, { status: 500 })
    renderAt('/trips')
    const form = await openProfileTab()

    fireEvent.click(within(form).getByRole('button', { name: 'Save' }))

    expect(await within(form).findByRole('alert')).toHaveTextContent('Something went wrong. Please try again in a moment.')
  })

  it('switches the interface to the saved language', async () => {
    renderAt('/trips')
    const form = await openProfileTab()

    fireEvent.change(within(form).getByLabelText('Language'), { target: { value: 'fr' } })
    fireEvent.click(within(form).getByRole('button', { name: 'Save' }))

    expect(await screen.findByRole('heading', { name: 'Mes aperçus' })).toBeInTheDocument()
    expect(patches()[0]?.body).toEqual({ first_name: 'Camille', last_name: 'Durand', locale: 'fr' })
    expect(await screen.findByRole('status')).toHaveTextContent('Vos informations sont enregistrées.')
    expect(screen.getByRole('form', { name: 'Informations personnelles' })).toBeInTheDocument()
  })
})
