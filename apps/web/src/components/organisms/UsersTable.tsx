import { useId } from 'react'
import { useTranslation } from 'react-i18next'

import { formatShortDate } from '@/lib/format'

import { ROLES, type Role } from './roles'

export type UserRow = {
  id: string
  name: string | null
  email: string
  role: Role
  email_verified: boolean
  created_at: string
}

type Props = {
  users: UserRow[]
  /** The signed-in admin: they cannot change their own role. */
  meId: string
  /** The user whose role is being saved. */
  savingId?: string
  onChangeRole: (userId: string, role: Role) => void
}

/** The users with their role, which an admin can change. */
export function UsersTable({ users, meId, savingId, onChangeRole }: Props) {
  const id = useId()
  const { t, i18n } = useTranslation('admin')
  return (
    <table className="w-full border-collapse border-t border-line text-sm">
      <caption className="sr-only">{t('table.caption')}</caption>
      <thead>
        <tr className="text-left text-xs tracking-widest text-muted uppercase">
          <th scope="col" className="p-4 font-normal">
            {t('table.user')}
          </th>
          <th scope="col" className="p-4 font-normal">
            {t('table.role')}
          </th>
          <th scope="col" className="hidden p-4 font-normal md:table-cell">
            {t('table.status')}
          </th>
          <th scope="col" className="hidden p-4 font-normal md:table-cell">
            {t('table.joined')}
          </th>
        </tr>
      </thead>
      <tbody>
        {users.map((user) => {
          const isMe = user.id === meId
          // Agent and admin need a verified email (enforced by the API too).
          const locked = isMe || !user.email_verified
          return (
            <tr key={user.id} className="border-t border-line">
              <th scope="row" className="p-4 text-left font-normal">
                <span className="grid">
                  <b className="font-semibold">{user.name ?? user.email}</b>
                  <small className="mt-1 text-xs text-muted">{user.email}</small>
                </span>
              </th>
              <td className="p-4">
                <label htmlFor={`${id}-${user.id}`} className="sr-only">
                  {t('table.roleOf', { name: user.name ?? user.email })}
                </label>
                <select
                  id={`${id}-${user.id}`}
                  value={user.role}
                  disabled={locked || savingId === user.id}
                  onChange={(event) => onChangeRole(user.id, event.target.value as Role)}
                  className="min-h-11 border border-line bg-white px-2.5 disabled:text-muted"
                >
                  {ROLES.map((role) => (
                    <option key={role} value={role}>
                      {t(`roles.${role}`)}
                    </option>
                  ))}
                </select>
              </td>
              <td className="hidden p-4 md:table-cell">
                <span
                  aria-hidden="true"
                  className={`mr-1.5 inline-block size-1.5 rounded-full ${user.email_verified ? 'bg-ok' : 'bg-pending'}`}
                />
                {isMe ? t('table.you') : user.email_verified ? t('table.verified') : t('table.pending')}
              </td>
              <td className="hidden p-4 md:table-cell">{formatShortDate(i18n.language, user.created_at)}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
