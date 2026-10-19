import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { getDbHealthOptions, getHealthOptions } from '../api/generated/@tanstack/react-query.gen'

/** Shows whether the API and its database answer. Useful to check the M0 setup. */
export function ApiStatus() {
  const api = useQuery(getHealthOptions())
  const db = useQuery(getDbHealthOptions())
  const { t } = useTranslation('status')

  return (
    <ul className="api-status" aria-label={t('label')}>
      <StatusRow line="api" ok={api.data?.status === 'ok'} pending={api.isPending} />
      <StatusRow line="database" ok={db.data?.status === 'ok'} pending={db.isPending} />
    </ul>
  )
}

function StatusRow({ line, ok, pending }: { line: 'api' | 'database'; ok: boolean; pending: boolean }) {
  const { t } = useTranslation('status')
  const state = t(pending ? 'checking' : ok ? 'ok' : 'unreachable')
  return (
    <li data-state={pending ? 'pending' : ok ? 'ok' : 'error'}>
      {t(line, { state })}
    </li>
  )
}
