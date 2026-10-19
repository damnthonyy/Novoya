import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, redirect } from '@tanstack/react-router'
import { useDeferredValue, useState } from 'react'

import {
  changeUserRoleMutation,
  listUsersOptions,
  listUsersQueryKey,
} from '../../api/generated/@tanstack/react-query.gen'
import { Eyebrow } from '../../components/atoms/Eyebrow'
import { Input } from '../../components/atoms/Input'
import { ErrorNote } from '../../components/molecules/ErrorNote'
import { BackofficeLayout } from '../../components/organisms/BackofficeLayout'
import { ROLE_LABELS, type Role } from '../../components/organisms/roleLabels'
import { UsersTable } from '../../components/organisms/UsersTable'
import { AppShell } from '../../components/templates/AppShell'
import { canOpen } from '../../domain/auth/roles'

export const Route = createFileRoute('/_authenticated/admin')({
  beforeLoad: ({ context }) => {
    if (!canOpen(context.me.role, 'admin')) throw redirect({ to: '/wish' })
  },
  component: AdminPage,
})

function AdminPage() {
  const { me } = Route.useRouteContext()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [role, setRole] = useState<Role | ''>('')
  const q = useDeferredValue(search.trim())

  const query = { q: q || undefined, role: role || undefined, limit: 50 }
  const users = useQuery({ ...listUsersOptions({ query }), placeholderData: keepPreviousData })
  const changeRole = useMutation({
    ...changeUserRoleMutation(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: listUsersQueryKey() }),
  })

  return (
    <AppShell>
      <BackofficeLayout
        area="Administration"
        items={[{ label: 'Utilisateurs', active: true }, { label: 'Partenaires' }, { label: 'Offres' }]}
      >
        <Eyebrow>Administration</Eyebrow>
        <h1 className="m-0 text-[39px] md:text-[50px]">Utilisateurs</h1>

        <div className="mt-10 mb-4 flex flex-col gap-2.5 md:flex-row">
          <label className="sr-only" htmlFor="admin-search">
            Rechercher par e-mail
          </label>
          <Input
            id="admin-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Rechercher par e-mail…"
            className="md:max-w-[350px]"
          />
          <label className="sr-only" htmlFor="admin-role">
            Filtrer par rôle
          </label>
          <select
            id="admin-role"
            value={role}
            onChange={(event) => setRole(event.target.value as Role | '')}
            className="min-h-11 border border-line bg-white px-3"
          >
            <option value="">Tous les rôles</option>
            {(Object.keys(ROLE_LABELS) as Role[]).map((value) => (
              <option key={value} value={value}>
                {ROLE_LABELS[value]}
              </option>
            ))}
          </select>
        </div>

        {changeRole.isError && (
          <p role="alert" className="mb-4 text-danger">
            Le rôle n’a pas pu être changé. Réessayez.
          </p>
        )}

        {users.isPending ? (
          <p className="py-6 text-muted">Chargement des utilisateurs…</p>
        ) : users.isError ? (
          <ErrorNote message="Impossible de charger les utilisateurs." onRetry={() => users.refetch()} />
        ) : users.data.length === 0 ? (
          <p className="py-6 text-muted">Aucun utilisateur ne correspond à cette recherche.</p>
        ) : (
          <UsersTable
            users={users.data}
            meId={me.id}
            savingId={changeRole.isPending ? changeRole.variables?.path.user_id : undefined}
            onChangeRole={(userId, next) => changeRole.mutate({ path: { user_id: userId }, body: { role: next } })}
          />
        )}
        <p className="mt-5 text-xs text-muted">
          Les rôles Agent et Admin sont disponibles uniquement pour les e-mails vérifiés. Vous ne pouvez pas modifier
          votre propre rôle.
        </p>
      </BackofficeLayout>
    </AppShell>
  )
}
