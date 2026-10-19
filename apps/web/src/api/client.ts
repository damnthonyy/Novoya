import { toApiError } from './errors'
import { client } from './generated/client.gen'

// Point the generated client at the backend. Set VITE_API_URL to override.
client.setConfig({
  baseUrl: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  credentials: 'include',
})

// Without this, a failed request throws only the parsed body, without its HTTP status.
client.interceptors.error.use(toApiError)
