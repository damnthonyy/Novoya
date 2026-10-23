import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from '@tanstack/react-router'
import { useTranslation } from 'react-i18next'

import { getMeQueryKey, updateMeMutation } from '../../api/generated/@tanstack/react-query.gen'
import { storeLocale } from '../../i18n/storedLocale'

/**
 * PATCH /me, and what follows a save: the interface switches to the saved language, this
 * browser remembers it, and everything that shows the user (/me, the signed-in layout) is
 * read again. The language switch and the personal information form both save with it.
 */
export function useUpdateMe() {
  const { i18n } = useTranslation()
  const queryClient = useQueryClient()
  const router = useRouter()
  return useMutation({
    ...updateMeMutation(),
    onSuccess: async (user) => {
      storeLocale(user.locale)
      queryClient.setQueryData(getMeQueryKey(), user)
      await i18n.changeLanguage(user.locale)
      await queryClient.invalidateQueries({ queryKey: getMeQueryKey() })
      // The signed-in layout keeps the user it loaded in the route context: reload it.
      await router.invalidate()
    },
  })
}
