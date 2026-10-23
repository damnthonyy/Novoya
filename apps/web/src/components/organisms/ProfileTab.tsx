import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { getMeOptions } from '../../api/generated/@tanstack/react-query.gen'
import { useAccountErrors } from '../../routes/-accountErrors'
import { useUpdateMe } from '../../hooks/i18n/useUpdateMe'
import { ProfileForm, type Profile } from './ProfileForm'

/** The "Personal information" tab on My trips: GET /me, saved with PATCH /me. */
export function ProfileTab() {
  const { t } = useTranslation('profile')
  // The signed-in guard has loaded /me already: this reads the cache and follows each save.
  const me = useQuery(getMeOptions())
  const save = useUpdateMe()
  const errors = useAccountErrors(save.error)

  if (!me.data) return null
  const profile: Profile = {
    firstName: me.data.first_name ?? '',
    lastName: me.data.last_name ?? '',
    locale: me.data.locale,
  }

  return (
    <ProfileForm
      profile={profile}
      email={me.data.email}
      onSubmit={async ({ firstName, lastName, locale }) => {
        const user = await save.mutateAsync({ body: { first_name: firstName, last_name: lastName, locale } })
        return { firstName: user.first_name ?? '', lastName: user.last_name ?? '', locale: user.locale }
      }}
      pending={save.isPending}
      errors={{ firstName: errors.firstName, lastName: errors.lastName, form: errors.form }}
      success={save.isSuccess ? t('saved') : undefined}
    />
  )
}
