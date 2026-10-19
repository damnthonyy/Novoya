import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'

import { ApiError } from '../../../api/errors'
import { sendWishMutation } from '../../../api/generated/@tanstack/react-query.gen'
import { type CachedWish, type WishResponse, wishQueryKey } from '../../../api/wishes'
import { Eyebrow } from '../../../components/atoms/Eyebrow'
import { Seal } from '../../../components/atoms/Seal'
import { CoverageSuggestions } from '../../../components/organisms/CoverageSuggestions'
import { WishComposer } from '../../../components/organisms/WishComposer'
import { AppShell } from '../../../components/templates/AppShell'
import { destinationLabel, destinationPhoto, suggestionWish } from '../../../domain/wish/destination'
import { sendWishErrorMessage, wishTextError } from '../../../domain/wish/wish'

export const Route = createFileRoute('/_authenticated/wish/')({
  component: WishPage,
})

const SPARKS = [
  ['Culture & calme', 'Quelques jours au soleil, entre culture et calme'],
  ['Océan & mouvement', 'Une parenthèse sportive face à l’océan'],
] as const

function WishPage() {
  const { me } = Route.useRouteContext()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const textarea = useRef<HTMLTextAreaElement>(null)
  const [text, setText] = useState('')
  const [checkError, setCheckError] = useState<string>()
  // The last answer that keeps the client on this page: not covered, or no place named.
  const [answer, setAnswer] = useState<WishResponse>()

  const send = useMutation({
    ...sendWishMutation(),
    onSuccess: async (wish) => {
      if (wish.status === 'panel_shown') {
        queryClient.setQueryData<CachedWish>(wishQueryKey(wish.id), { ...wish, text: text.trim() })
        await navigate({ to: '/wish/$wishId/preferences', params: { wishId: wish.id } })
        return
      }
      setAnswer(wish)
    },
  })

  const submit = () => {
    const error = wishTextError(text)
    setCheckError(error ?? undefined)
    if (!error) send.mutate({ body: { text: text.trim() } })
  }

  const startOver = (nextText: string) => {
    setAnswer(undefined)
    send.reset()
    setText(nextText)
    // After the view switches back, put the cursor at the end of the text.
    requestAnimationFrame(() => {
      textarea.current?.focus()
      textarea.current?.setSelectionRange(nextText.length, nextText.length)
    })
  }

  if (answer?.status === 'not_covered') {
    return (
      <AppShell>
        <main>
          <CoverageSuggestions
            place={answer.destination ? (answer.destination.city ?? answer.destination.country) : 'Cette destination'}
            suggestions={answer.suggestions.map((destination) => ({
              key: destinationLabel(destination),
              label: destinationLabel(destination),
              image: destinationPhoto(destination),
              onPick: () => startOver(suggestionWish(destination)),
            }))}
            onRephrase={() => startOver(text)}
          />
        </main>
      </AppShell>
    )
  }

  const sendError = send.isError
    ? sendWishErrorMessage(send.error instanceof ApiError ? send.error.code : undefined)
    : undefined
  const firstName = me.name?.trim().split(/\s+/)[0]

  return (
    <AppShell tone="ivory">
      <main className="flex min-h-[calc(100vh-72px)] flex-col items-center justify-center px-[18px] py-10 text-center md:min-h-[calc(100vh-88px)] md:px-5 md:py-[70px]">
        <Seal className="mb-5 size-[57px] text-2xl shadow-[0_0_0_10px_rgb(239_118_94/0.07)]" />
        <Eyebrow>{firstName ? `Bonjour ${firstName}` : 'Bonjour'}</Eyebrow>
        <h1 className="mb-[23px] text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
          De quoi avez-vous
          <br />
          <em>envie, vraiment ?</em>
        </h1>
        <p className="mb-8 text-muted">Un lieu, une sensation, un rythme… Écrivez comme cela vous vient.</p>
        {answer?.status === 'draft' && (
          <p role="status" className="mb-4 max-w-[760px] text-ink">
            Où aimeriez-vous partir ? Ajoutez une ville ou un pays à votre envie.
          </p>
        )}
        <WishComposer
          value={text}
          onChange={(value) => {
            setText(value)
            if (checkError) setCheckError(undefined)
          }}
          onSubmit={submit}
          pending={send.isPending}
          error={checkError ?? sendError}
          textareaRef={textarea}
        />
        <div className="mt-[22px] flex w-full items-center justify-start gap-2.5 overflow-x-auto md:w-auto md:justify-center">
          <span className="hidden text-xs text-muted md:inline">
            {answer?.status === 'draft' && answer.suggestions.length > 0
              ? 'Nos destinations :'
              : 'Besoin d’une étincelle ?'}
          </span>
          {(answer?.status === 'draft' && answer.suggestions.length > 0
            ? answer.suggestions.map((destination) => [destinationLabel(destination), suggestionWish(destination)] as const)
            : SPARKS
          ).map(([label, wish]) => (
            <button
              key={label}
              type="button"
              onClick={() => startOver(wish)}
              className="min-h-11 shrink-0 rounded-full border border-line px-[13px] py-2 text-xs"
            >
              {label}
            </button>
          ))}
        </div>
        <p className="mt-10 text-xs text-muted">✦ Vos mots restent chez Novoya. Aucun import, jamais.</p>
      </main>
    </AppShell>
  )
}
