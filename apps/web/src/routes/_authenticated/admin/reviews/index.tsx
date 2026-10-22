import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  listAllReviewsOptions,
  listAllReviewsQueryKey,
  listReviewsQueryKey,
  updateReviewMutation,
} from '../../../../api/generated/@tanstack/react-query.gen'
import type { AdminReviewResponse } from '../../../../api/generated/types.gen'
import { Eyebrow } from '../../../../components/atoms/Eyebrow'
import { ErrorNote } from '../../../../components/molecules/ErrorNote'
import { ReviewsTable } from '../../../../components/organisms/ReviewsTable'

export const Route = createFileRoute('/_authenticated/admin/reviews/')({
  component: ReviewsPage,
})

/** Every published review, including hidden ones. The switch hides it from GET /reviews. */
function ReviewsPage() {
  const { t } = useTranslation('admin')
  const queryClient = useQueryClient()
  const reviews = useQuery(listAllReviewsOptions())
  const [savingIds, setSavingIds] = useState<ReadonlySet<string>>(new Set())
  const [failedIds, setFailedIds] = useState<ReadonlySet<string>>(new Set())
  const toggle = useMutation({
    ...updateReviewMutation(),
    onMutate: ({ path }) => {
      setSavingIds((ids) => withId(ids, path.review_id))
      setFailedIds((ids) => withoutId(ids, path.review_id))
    },
    onError: (_error, { path }) => setFailedIds((ids) => withId(ids, path.review_id)),
    onSuccess: (saved: AdminReviewResponse) => {
      queryClient.setQueryData(listAllReviewsQueryKey(), (rows: AdminReviewResponse[] | undefined) =>
        rows?.map((row) => (row.id === saved.id ? saved : row)),
      )
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: listAllReviewsQueryKey() }),
        queryClient.invalidateQueries({ queryKey: listReviewsQueryKey() }),
      ])
    },
    onSettled: (_data, _error, { path }) => setSavingIds((ids) => withoutId(ids, path.review_id)),
  })

  return (
    <>
      <Eyebrow>{t('eyebrow')}</Eyebrow>
      <h1 className="m-0 text-[39px] md:text-[50px]">{t('reviews.title')}</h1>
      {failedIds.size > 0 && (
        <p role="alert" className="mt-4 text-danger">
          {t('reviews.switchFailed')}
        </p>
      )}
      {reviews.isPending ? (
        <p className="py-6 text-muted">{t('reviews.loading')}</p>
      ) : !reviews.data ? (
        <ErrorNote message={t('reviews.loadFailed')} onRetry={() => reviews.refetch()} />
      ) : reviews.data.length === 0 ? (
        <p className="py-6 text-muted">{t('reviews.empty')}</p>
      ) : (
        <div className="mt-10 overflow-x-auto">
          <ReviewsTable
            reviews={reviews.data}
            savingIds={savingIds}
            onHide={(reviewId, hidden) => toggle.mutate({ path: { review_id: reviewId }, body: { hidden } })}
          />
        </div>
      )}
    </>
  )
}

function withId(ids: ReadonlySet<string>, id: string): ReadonlySet<string> {
  return new Set(ids).add(id)
}

function withoutId(ids: ReadonlySet<string>, id: string): ReadonlySet<string> {
  const next = new Set(ids)
  next.delete(id)
  return next
}
