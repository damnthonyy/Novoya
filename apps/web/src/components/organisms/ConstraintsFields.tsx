import { useId } from 'react'
import { useTranslation } from 'react-i18next'

import { Eyebrow } from '../atoms/Eyebrow'
import { Input } from '../atoms/Input'
import { Field } from '../molecules/Field'
import { Stepper } from '../molecules/Stepper'

export type ConstraintsValues = { budget: string; persons: number; startDate: string; endDate: string }

type Props = {
  values: ConstraintsValues
  errors: Partial<Record<keyof ConstraintsValues, string>>
  onChange: (values: ConstraintsValues) => void
  minPersons: number
  maxPersons: number
}

const label = 'text-xs tracking-[0.12em] uppercase'

/** The panel's last step: budget, travellers and dates. */
export function ConstraintsFields({ values, errors, onChange, minPersons, maxPersons }: Props) {
  const personsId = useId()
  const { t } = useTranslation('preferences')
  const set = <K extends keyof ConstraintsValues>(key: K, value: ConstraintsValues[K]) =>
    onChange({ ...values, [key]: value })

  return (
    <section aria-labelledby={`${personsId}-title`} className="mt-[50px] border-t border-ink pt-10">
      <Eyebrow>
        <span id={`${personsId}-title`}>{t('lastMarkers')}</span>
      </Eyebrow>
      <div className="grid gap-x-5 md:grid-cols-2">
        <Field
          label={<span className={label}>{t('budget')}</span>}
          hint={t('budgetHint')}
          error={errors.budget}
          className="my-2.5"
        >
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              inputMode="decimal"
              placeholder={t('budgetPlaceholder')}
              aria-describedby={describedBy}
              aria-invalid={invalid}
              value={values.budget}
              onChange={(event) => set('budget', event.target.value)}
            />
          )}
        </Field>
        <div className="my-2.5">
          <p id={`${personsId}-label`} className={`mb-2 ${label}`}>
            {t('travellers')}
          </p>
          <div aria-labelledby={`${personsId}-label`} role="group">
            <Stepper
              value={values.persons}
              min={minPersons}
              max={maxPersons}
              decreaseLabel={t('fewerTravellers')}
              increaseLabel={t('moreTravellers')}
              valueText={t('persons', { count: values.persons })}
              describedBy={errors.persons ? `${personsId}-error` : undefined}
              onChange={(persons) => set('persons', persons)}
            />
          </div>
          {errors.persons && (
            <p id={`${personsId}-error`} className="mt-1.5 text-sm text-danger">
              {errors.persons}
            </p>
          )}
        </div>
        <Field label={<span className={label}>{t('departure')}</span>} error={errors.startDate} className="my-2.5">
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              type="date"
              aria-describedby={describedBy}
              aria-invalid={invalid}
              value={values.startDate}
              onChange={(event) => set('startDate', event.target.value)}
            />
          )}
        </Field>
        <Field label={<span className={label}>{t('return')}</span>} error={errors.endDate} className="my-2.5">
          {({ id, describedBy, invalid }) => (
            <Input
              id={id}
              type="date"
              min={values.startDate || undefined}
              aria-describedby={describedBy}
              aria-invalid={invalid}
              value={values.endDate}
              onChange={(event) => set('endDate', event.target.value)}
            />
          )}
        </Field>
      </div>
    </section>
  )
}
