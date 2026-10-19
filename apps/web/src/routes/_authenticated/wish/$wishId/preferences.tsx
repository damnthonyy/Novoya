import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { type FormEvent, useState } from 'react'

import { ApiError } from '../../../../api/errors'
import { answerPanelMutation } from '../../../../api/generated/@tanstack/react-query.gen'
import type { PanelOut } from '../../../../api/generated/types.gen'
import { type CachedWish, wishQueryKey } from '../../../../api/wishes'
import { Button } from '../../../../components/atoms/Button'
import { Eyebrow } from '../../../../components/atoms/Eyebrow'
import { TagGroup } from '../../../../components/molecules/TagGroup'
import { ConstraintsFields, type ConstraintsValues } from '../../../../components/organisms/ConstraintsFields'
import { IntentAside } from '../../../../components/organisms/IntentAside'
import { StickyAction } from '../../../../components/organisms/StickyAction'
import { AppShell } from '../../../../components/templates/AppShell'
import {
  constraintsErrors,
  type ConstraintsErrors,
  MAX_PERSONS,
  MIN_PERSONS,
  parseBudget,
  personsLabel,
} from '../../../../domain/constraints/constraints'
import {
  answerPanelErrorMessage,
  initialSelection,
  type Selection,
  selectedTags,
  toggleTag,
} from '../../../../domain/panel/selection'

export const Route = createFileRoute('/_authenticated/wish/$wishId/preferences')({
  component: PreferencesPage,
})

const STEPS = ['Préférences', 'Aperçu', 'Devis']
const FORM_ID = 'preferences-form'

function PreferencesPage() {
  const { wishId } = Route.useParams()
  const wish = useQueryClient().getQueryData<CachedWish>(wishQueryKey(wishId))

  return (
    <AppShell>
      {wish?.panel ? (
        <PreferencesForm wishId={wishId} text={wish.text} panel={wish.panel} />
      ) : (
        <main className="mx-auto max-w-xl px-5 py-24 text-center">
          <Eyebrow>Préférences</Eyebrow>
          <h1 className="mb-4 text-[47px] leading-none">Reprenons depuis votre envie.</h1>
          <p className="mb-8 text-muted">
            Nous ne retrouvons pas le panneau de cette envie sur cette page. Décrivez-la à nouveau : cela ne
            prend qu’un instant.
          </p>
          <Button asChild variant="coral" size="lg">
            <Link to="/wish">Décrire mon voyage</Link>
          </Button>
        </main>
      )}
    </AppShell>
  )
}

function PreferencesForm({ wishId, text, panel }: { wishId: string; text: string; panel: PanelOut }) {
  const navigate = useNavigate()
  const [selection, setSelection] = useState<Selection>(() => initialSelection(panel.sections))
  const [constraints, setConstraints] = useState<ConstraintsValues>({
    budget: '',
    persons: 2,
    startDate: '',
    endDate: '',
  })
  const [errors, setErrors] = useState<ConstraintsErrors>({})

  const answer = useMutation({
    ...answerPanelMutation(),
    onSuccess: () => navigate({ to: '/wish/$wishId/building', params: { wishId } }),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const found = constraintsErrors(constraints)
    setErrors(found)
    if (Object.keys(found).length > 0 || answer.isPending) return
    answer.mutate({
      path: { wish_id: wishId },
      body: {
        selected_tags: selectedTags(selection),
        budget_max: parseBudget(constraints.budget)!,
        currency: 'EUR',
        persons: constraints.persons,
        start_date: constraints.startDate,
        end_date: constraints.endDate,
      },
    })
  }

  const labels = new Map(panel.sections.flatMap((section) => section.tags.map((tag) => [`${section.id}:${tag.id}`, tag.label])))
  const picked = selectedTags(selection).map(({ section, tag }) => labels.get(`${section}:${tag}`) ?? tag)

  return (
    <div className="md:grid md:min-h-[calc(100vh-88px)] md:grid-cols-[33%_67%]">
      <IntentAside wish={text} steps={STEPS} current={0} />
      <main className="bg-paper px-5 pt-[55px] pb-[155px] md:px-[8vw] md:pt-20 md:pb-40">
        <Eyebrow>Étape 1 sur 3</Eyebrow>
        <h1 className="mb-[23px] text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
          Ce qui compte
          <br />
          <em>pour vous.</em>
        </h1>
        <p className="text-muted">Choisissez ce qui vous parle. Vous pouvez aussi ne rien sélectionner.</p>
        <form id={FORM_ID} onSubmit={submit} noValidate>
          {panel.sections.map((section) => (
            <TagGroup
              key={section.id}
              title={section.title}
              multi={section.multi}
              tags={section.tags}
              selected={selection[section.id] ?? []}
              onToggle={(tagId) => setSelection((current) => toggleTag(current, section, tagId))}
            />
          ))}
          <ConstraintsFields
            values={constraints}
            errors={errors}
            onChange={(values) => {
              setConstraints(values)
              if (Object.keys(errors).length > 0) setErrors(constraintsErrors(values))
            }}
            minPersons={MIN_PERSONS}
            maxPersons={MAX_PERSONS}
            personsText={personsLabel(constraints.persons)}
          />
          {answer.isError && (
            <p role="alert" className="mt-6 text-danger">
              {answerPanelErrorMessage(answer.error instanceof ApiError ? answer.error.code : undefined)}
            </p>
          )}
        </form>
      </main>
      <StickyAction
        summary={`${picked.length} préférence${picked.length > 1 ? 's' : ''}`}
        chips={picked.slice(0, 3)}
        action={
          <Button type="submit" form={FORM_ID} variant="coral" size="lg" className="w-full md:w-auto" disabled={answer.isPending}>
            {answer.isPending ? 'Envoi…' : 'Composer mon aperçu'} <span aria-hidden="true">↗</span>
          </Button>
        }
      />
    </div>
  )
}
