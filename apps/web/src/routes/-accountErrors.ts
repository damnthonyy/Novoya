import { useTranslation } from 'react-i18next'

import { ApiError } from '../api/errors'
import { accountError, type AccountErrorField } from '../domain/auth/errors'

type AccountErrors = Partial<Record<AccountErrorField | 'form', string>>

/**
 * The message of a failed account request (sign-up, reset, change of password), translated,
 * under the field it belongs to, or `form` for the others. Empty without an error.
 */
export function useAccountErrors(error: unknown): AccountErrors {
  const { t } = useTranslation('errors')
  if (!error) return {}
  const { key, field } = accountError(error instanceof ApiError ? error.code : undefined)
  return { [field ?? 'form']: t(key) }
}
