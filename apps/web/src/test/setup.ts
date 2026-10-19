import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

import i18n from '../i18n'

// Vitest runs without globals, so Testing Library cannot unmount between tests by itself.
// Tests are written against the English texts: switch back after a test that changed it.
afterEach(async () => {
  cleanup()
  await i18n.changeLanguage('en')
})
