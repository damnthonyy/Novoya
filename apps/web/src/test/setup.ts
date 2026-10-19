import '@testing-library/jest-dom/vitest'

import { cleanup, configure } from '@testing-library/react'
import { afterEach } from 'vitest'

import i18n from '../i18n'

// The first render of a route chunk can take over 1 s on a cold run (CI, a fresh Docker image).
configure({ asyncUtilTimeout: 3000 })

// Vitest runs without globals, so Testing Library cannot unmount between tests by itself.
// Tests are written against the English texts: switch back after a test that changed it.
afterEach(async () => {
  cleanup()
  await i18n.changeLanguage('en')
})
