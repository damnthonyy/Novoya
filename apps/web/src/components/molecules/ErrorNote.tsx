import { Button } from '../atoms/Button'

type Props = {
  message: string
  onRetry?: () => void
  retryLabel?: string
}

/** Something failed that the user did not cause, with a way to try again. */
export function ErrorNote({ message, onRetry, retryLabel = 'Réessayer' }: Props) {
  return (
    <div role="alert" className="mx-auto mt-8 max-w-lg px-5">
      <p className="mb-4 text-danger">{message}</p>
      {onRetry && <Button onClick={onRetry}>{retryLabel}</Button>}
    </div>
  )
}
