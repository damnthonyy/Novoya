import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, RouterProvider } from '@tanstack/react-router'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import '../api/client'
import { client } from '../api/generated/client.gen'
import type { MeResponse, WishResponse } from '../api/generated/types.gen'
import { type CachedWish, wishQueryKey } from '../api/wishes'
import { createAppRouter } from '../router'

const CAMILLE: MeResponse = {
  id: '6f1c2b1e-0000-4000-8000-000000000002',
  email: 'camille@exemple.fr',
  name: 'Camille Martin',
  role: 'client',
  locale: 'fr',
  status: 'active',
  email_verified: true,
  created_at: '2026-10-01T10:00:00Z',
  sign_in_methods: ['password'],
}

const WISH_ID = '0b5f8a52-0000-4000-8000-000000000010'

const PANEL_WISH: WishResponse = {
  id: WISH_ID,
  status: 'panel_shown',
  destination: { country: 'Greece', city: 'Chania' },
  suggestions: [],
  panel: {
    ask_budget: true,
    ask_persons: true,
    ask_dates: true,
    sections: [
      {
        id: 'mood',
        title: 'Ambiance',
        multi: true,
        tags: [
          { id: 'calm', label: 'Calme', preselected: true },
          { id: 'culture', label: 'Culture', preselected: false },
        ],
      },
      {
        id: 'pace',
        title: 'Rythme',
        multi: false,
        tags: [
          { id: 'slow', label: 'Très doux', preselected: false },
          { id: 'busy', label: 'Dynamique', preselected: false },
        ],
      },
    ],
  },
}

const NOT_COVERED: WishResponse = {
  id: '0b5f8a52-0000-4000-8000-000000000011',
  status: 'not_covered',
  destination: { country: 'Japan', city: 'Kyoto' },
  suggestions: [
    { country: 'Greece', city: 'Chania' },
    { country: 'Morocco', city: 'Marrakech' },
  ],
  panel: null,
}

type Call = { method: string; path: string; body: unknown }

let signedIn: MeResponse | null
let calls: Call[]
let wishAnswer: () => Response
let loginAnswer: () => Response
let answersAnswer: () => Response

function mockApi() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const request = input instanceof Request ? input : new Request(String(input))
    const path = new URL(request.url).pathname
    const text = request.method === 'POST' ? await request.text() : ''
    calls.push({ method: request.method, path, body: text ? JSON.parse(text) : undefined })
    if (path === '/me') {
      return signedIn
        ? Response.json(signedIn)
        : Response.json({ code: 'unauthenticated', detail: 'not signed in' }, { status: 401 })
    }
    if (path === '/auth/login') return loginAnswer()
    if (path === '/wishes') return wishAnswer()
    if (path === `/wishes/${WISH_ID}/answers`) return answersAnswer()
    return Response.json({ status: 'ok' })
  })
}

function renderAt(url: string, prepare?: (queryClient: QueryClient) => void) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  prepare?.(queryClient)
  const router = createAppRouter(queryClient, createMemoryHistory({ initialEntries: [url] }))
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { router, queryClient }
}

const posts = (path: string) => calls.filter((call) => call.method === 'POST' && call.path === path)

beforeEach(() => {
  client.setConfig({ baseUrl: 'http://api.test' })
  signedIn = CAMILLE
  calls = []
  wishAnswer = () => Response.json(PANEL_WISH, { status: 201 })
  loginAnswer = () => new Response(null, { status: 204 })
  answersAnswer = () => Response.json({ id: WISH_ID, status: 'answered' })
  mockApi()
})
afterEach(() => {
  vi.restoreAllMocks()
})

describe('signing in with an e-mail and a password', () => {
  async function fillAndSend(password: string) {
    fireEvent.change(await screen.findByLabelText('E-mail'), { target: { value: ' camille@exemple.fr ' } })
    fireEvent.change(screen.getByLabelText('Mot de passe'), { target: { value: password } })
    fireEvent.click(screen.getByRole('button', { name: /^Se connecter/ }))
  }

  it('signs in and goes to the requested page', async () => {
    signedIn = null
    loginAnswer = () => {
      signedIn = CAMILLE
      return new Response(null, { status: 204 })
    }
    const { router } = renderAt('/login?redirect=%2Fwish%3Ffrom%3Dlogin')

    await fillAndSend('correct horse')

    expect(await screen.findByRole('heading', { name: /De quoi avez-vous/ })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/wish')
    expect(posts('/auth/login')[0]!.body).toEqual({ email: 'camille@exemple.fr', password: 'correct horse' })
  })

  it('says so when the password is wrong, and stays on the page', async () => {
    signedIn = null
    loginAnswer = () => Response.json({ code: 'invalid_credentials', detail: 'nope' }, { status: 401 })
    const { router } = renderAt('/login')

    await fillAndSend('wrong')

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou mot de passe incorrect.')
    expect(router.state.location.pathname).toBe('/login')
  })

  it('asks to confirm the e-mail first when it is not verified', async () => {
    signedIn = null
    loginAnswer = () => Response.json({ code: 'email_not_verified', detail: 'verify' }, { status: 403 })
    renderAt('/login')

    await fillAndSend('correct horse')

    expect(await screen.findByRole('alert')).toHaveTextContent('Confirmez d’abord votre adresse e-mail')
  })
})

describe('sending a wish', () => {
  async function writeAndSend(text: string) {
    fireEvent.change(await screen.findByLabelText('Votre envie de voyage'), { target: { value: text } })
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }))
  }

  it('greets the client by first name', async () => {
    renderAt('/wish')
    expect(await screen.findByText('Bonjour Camille')).toBeInTheDocument()
  })

  it('does not send an empty wish', async () => {
    renderAt('/wish')

    await writeAndSend('   ')

    expect(await screen.findByRole('alert')).toHaveTextContent('Décrivez votre envie')
    expect(posts('/wishes')).toHaveLength(0)
  })

  it('sends with Ctrl + Enter', async () => {
    renderAt('/wish')
    const box = await screen.findByLabelText('Votre envie de voyage')
    fireEvent.change(box, { target: { value: 'La Crète en mai' } })

    fireEvent.keyDown(box, { key: 'Enter', ctrlKey: true })

    await waitFor(() => expect(posts('/wishes')).toHaveLength(1))
    expect(posts('/wishes')[0]!.body).toEqual({ text: 'La Crète en mai' })
  })

  it('opens the preferences when the destination is covered, keeping the wish for that page', async () => {
    const { router, queryClient } = renderAt('/wish')

    await writeAndSend('  Une semaine calme à Chania  ')

    expect(await screen.findByRole('heading', { name: /Ce qui compte/ })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(`/wish/${WISH_ID}/preferences`)
    expect(queryClient.getQueryData<CachedWish>(wishQueryKey(WISH_ID))?.text).toBe('Une semaine calme à Chania')
    expect(screen.getByText('“Une semaine calme à Chania”')).toBeInTheDocument()
  })

  it('says when the destination is not covered and suggests covered ones', async () => {
    wishAnswer = () => Response.json(NOT_COVERED, { status: 201 })
    renderAt('/wish')

    await writeAndSend('Le Japon au printemps')

    expect(await screen.findByRole('heading', { name: /Kyoto nous fait rêver aussi/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Chania · Greece/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Marrakech · Morocco/ })).toBeInTheDocument()
  })

  it('starts a new wish from a suggestion', async () => {
    wishAnswer = () => Response.json(NOT_COVERED, { status: 201 })
    renderAt('/wish')
    await writeAndSend('Le Japon au printemps')

    fireEvent.click(await screen.findByRole('button', { name: /Marrakech · Morocco/ }))

    expect(await screen.findByLabelText('Votre envie de voyage')).toHaveValue('Quelques jours à Marrakech, ')
  })

  it('asks where when the wish names no place', async () => {
    wishAnswer = () =>
      Response.json({ id: 'x', status: 'draft', destination: null, suggestions: [], panel: null }, { status: 201 })
    renderAt('/wish')

    await writeAndSend('Quelque part au calme')

    expect(await screen.findByRole('status')).toHaveTextContent('Où aimeriez-vous partir ?')
  })

  it('explains a failure and lets the client try again', async () => {
    wishAnswer = () => Response.json({ code: 'internal_error', detail: 'boom' }, { status: 500 })
    renderAt('/wish')

    await writeAndSend('La Crète en mai')

    expect(await screen.findByRole('alert')).toHaveTextContent('n’a pas pu être envoyée')
    expect(screen.getByLabelText('Votre envie de voyage')).toHaveValue('La Crète en mai')
  })
})

describe('the preferences panel', () => {
  const withWish = (queryClient: QueryClient) =>
    queryClient.setQueryData<CachedWish>(wishQueryKey(WISH_ID), { ...PANEL_WISH, text: 'Une semaine à Chania' })

  function fillConstraints() {
    fireEvent.change(screen.getByLabelText(/Budget maximum/), { target: { value: '3 500 €' } })
    fireEvent.change(screen.getByLabelText('Départ'), { target: { value: '2026-05-12' } })
    fireEvent.change(screen.getByLabelText('Retour'), { target: { value: '2026-05-19' } })
  }

  it('starts from the preselected tags and sends the chosen tags and constraints', async () => {
    const { router } = renderAt(`/wish/${WISH_ID}/preferences`, withWish)

    expect(await screen.findByRole('button', { name: /Calme/ })).toHaveAttribute('aria-pressed', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Culture' }))
    fireEvent.click(screen.getByRole('button', { name: 'Très doux' }))
    fireEvent.click(screen.getByRole('button', { name: 'Dynamique' })) // single choice: replaces "Très doux"
    fireEvent.click(screen.getByRole('button', { name: 'Un voyageur de plus' }))
    fillConstraints()
    fireEvent.click(screen.getByRole('button', { name: /Composer mon aperçu/ }))

    await waitFor(() => expect(router.state.location.pathname).toBe(`/wish/${WISH_ID}/building`))
    expect(posts(`/wishes/${WISH_ID}/answers`)[0]!.body).toEqual({
      selected_tags: [
        { section: 'mood', tag: 'calm' },
        { section: 'mood', tag: 'culture' },
        { section: 'pace', tag: 'busy' },
      ],
      budget_max: '3500.00',
      currency: 'EUR',
      persons: 3,
      start_date: '2026-05-12',
      end_date: '2026-05-19',
    })
    expect(await screen.findByRole('heading', { name: /On cale les soirées/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Voir mes voyages/ })).toHaveAttribute('href', '/trips')
  })

  it('checks the constraints before sending', async () => {
    renderAt(`/wish/${WISH_ID}/preferences`, withWish)
    await screen.findByRole('heading', { name: /Ce qui compte/ })
    fillConstraints()
    fireEvent.change(screen.getByLabelText('Retour'), { target: { value: '2026-05-01' } })

    fireEvent.click(screen.getByRole('button', { name: /Composer mon aperçu/ }))

    expect(await screen.findByText('Le retour doit être après le départ.')).toBeInTheDocument()
    expect(screen.getByLabelText('Retour')).toHaveAttribute('aria-invalid', 'true')
    expect(posts(`/wishes/${WISH_ID}/answers`)).toHaveLength(0)
  })

  it('explains an answer the API refuses', async () => {
    answersAnswer = () => Response.json({ code: 'invalid_answers', detail: 'bad tag' }, { status: 422 })
    renderAt(`/wish/${WISH_ID}/preferences`, withWish)
    await screen.findByRole('heading', { name: /Ce qui compte/ })
    fillConstraints()

    fireEvent.click(screen.getByRole('button', { name: /Composer mon aperçu/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Vérifiez les dates et le budget')
  })

  it('sends back to the wish when the panel is no longer known (page reloaded)', async () => {
    renderAt(`/wish/${WISH_ID}/preferences`)

    expect(await screen.findByRole('heading', { name: 'Reprenons depuis votre envie.' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Décrire mon voyage' })).toHaveAttribute('href', '/wish')
  })
})

describe('the landing page', () => {
  it('shows the public page to visitors, with a way to sign in', async () => {
    signedIn = null
    renderAt('/')

    expect(await screen.findByRole('heading', { name: /Votre envie/ })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Se connecter' })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: /Continuer avec Google/ })).toHaveAttribute(
      'href',
      'http://api.test/auth/google/login?redirect_to=%2Fwish',
    )
  })

  it('offers the client space to a signed-in visitor', async () => {
    renderAt('/')

    expect(await screen.findByRole('link', { name: 'Mon espace' })).toHaveAttribute('href', '/wish')
    expect(screen.queryByRole('link', { name: /Continuer avec Google/ })).not.toBeInTheDocument()
  })
})
