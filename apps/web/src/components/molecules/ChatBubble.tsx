import { cn } from '@/lib/utils'

/** One message in a conversation with the concierge. */
export function ChatBubble({ from, text }: { from: 'you' | 'novoya'; text: string }) {
  return (
    <p
      className={cn(
        'mb-2 max-w-[85%] px-3 py-2.5 text-xs leading-normal',
        from === 'you' ? 'ml-auto bg-ink text-white' : 'border border-line bg-white',
      )}
    >
      <span className="sr-only">{from === 'you' ? 'Vous : ' : 'Novoya : '}</span>
      {text}
    </p>
  )
}
