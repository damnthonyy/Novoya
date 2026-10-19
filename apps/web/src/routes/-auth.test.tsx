import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getMeQueryKey } from '../api/generated/@tanstack/react-query.gen'
import { client } from '../api/generated/client.gen'
import type { MeResponse } from '../api/generated/types.gen'
import { routeTree } from '../routeTree.gen'

const LEA: MeResponse = {
  id: '6f1c2b1e-0000-4000-8000-000000000001',
  email: 'lea@example.com',
  name: 'Léa Martin',
  role: 'client',
  locale: 'fr',
  status: 'active',
  email_verified: true,
  created_at: '2026-10-01T10:00:00Z',
  sign_in_methods: ['google'],
}

let signedIn: MeResponse | null
let calls: string[]

function mockApi() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const path = new URL(request.url).pathname
    calls.push(`${request.method} ${path}`)
    if (path === '/me') {
      return signedIn
        ? Response.json(signedIn)
        : Response.json({ code: 'unauthenticated', message: 'Sign in first' }, { status: 401 })
    }
    if (path === '/auth/logout') {
      signedIn = null
      return new Response(null, { status: 204 })
    }
    return Response.json({ status: 'ok' })
  })
}

function renderAt(url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const router = createRouter({
    routeTree,
    context: { queryClient },
    history: createMemoryHistory({ initialEntries: [url] }),
  })
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { router, queryClient }
}

describe('sign-in and sign-out', () => {
  beforeEach(() => {
    client.setConfig({ baseUrl: 'http://api.test' })
    signedIn = null
    calls = []
    mockApi()
  })
  afterEach(() => vi.restoreAllMocks())

  it('sends a signed-out visitor of a protected page to the login page', async () => {
    const { router } = renderAt('/')

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/login')
    expect(router.state.location.search).toEqual({ redirect: '/' })
  })

  it('starts Google sign-in and comes back to the requested page', async () => {
    renderAt('/login?redirect=%2Fwishes%3Fid%3D1')

    const link = await screen.findByRole('link', { name: 'Continue with Google' })
    expect(link).toHaveAttribute(
      'href',
      'http://api.test/auth/google/login?redirect_to=%2Fwishes%3Fid%3D1',
    )
  })

  it('never sends the user to another site after signing in', async () => {
    renderAt('/login?redirect=%2F%2Fevil.com')

    const link = await screen.findByRole('link', { name: 'Continue with Google' })
    expect(link).toHaveAttribute('href', 'http://api.test/auth/google/login?redirect_to=%2F')
  })

  it('explains why a Google sign-in failed', async () => {
    renderAt('/login?error=oauth_failed')

    expect(await screen.findByRole('alert')).toHaveTextContent('Google sign-in did not work')
  })

  it('skips the login page when already signed in', async () => {
    signedIn = LEA
    const { router } = renderAt('/login')

    expect(await screen.findByRole('heading', { name: 'Plan your next trip' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/')
  })

  it('shows the signed-in user in the header', async () => {
    signedIn = LEA
    renderAt('/')

    expect(await screen.findByText('Léa Martin')).toBeInTheDocument()
  })

  it('shows the email when the user has no name', async () => {
    signedIn = { ...LEA, name: null }
    renderAt('/')

    expect(await screen.findByText('lea@example.com')).toBeInTheDocument()
  })

  it('signs out, forgets the user and returns to the login page', async () => {
    signedIn = LEA
    const { router, queryClient } = renderAt('/')

    fireEvent.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(calls).toContain('POST /auth/logout')
    expect(router.state.location.pathname).toBe('/login')
    expect(screen.queryByText('Léa Martin')).not.toBeInTheDocument()
    expect(queryClient.getQueryData(getMeQueryKey())).toBeUndefined()
  })
})
