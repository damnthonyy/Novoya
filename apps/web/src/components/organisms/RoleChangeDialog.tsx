import { useTranslation } from 'react-i18next'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../ui/alert-dialog'
import type { Role } from './roles'

export type RoleChange = { userId: string; name: string; from: Role; to: Role }

type Props = {
  /** The change waiting for confirmation, or null when there is none. */
  change: RoleChange | null
  onConfirm: (change: RoleChange) => void
  onCancel: () => void
}

/**
 * Asks before a role changes. A role gives access to the agency or the administration, and a
 * closed <select> can change value from the keyboard alone, so nothing is sent without this step.
 */
export function RoleChangeDialog({ change, onConfirm, onCancel }: Props) {
  const { t } = useTranslation('admin')
  return (
    <AlertDialog open={change !== null} onOpenChange={(open) => !open && onCancel()}>
      {change && (
        <AlertDialogContent className="rounded-none border-line bg-white">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-serif text-2xl font-normal tracking-normal">
              {t('confirm.title', { name: change.name })}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-muted">
              {t('confirm.body', {
                name: change.name,
                from: t(`roles.${change.from}`),
                to: t(`roles.${change.to}`),
              })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="min-h-11 rounded-full">{t('confirm.cancel')}</AlertDialogCancel>
            <AlertDialogAction className="min-h-11 rounded-full" onClick={() => onConfirm(change)}>
              {t('confirm.action')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      )}
    </AlertDialog>
  )
}
