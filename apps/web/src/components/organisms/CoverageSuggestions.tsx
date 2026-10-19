import { Button } from '../atoms/Button'
import { Eyebrow } from '../atoms/Eyebrow'

type Suggestion = { key: string; label: string; image: string; onPick: () => void }

type Props = {
  /** The place the client asked for, as the API read it ("Japan"). */
  place: string
  suggestions: Suggestion[]
  onRephrase: () => void
}

/** Shown when no partner covers the place asked for: say so, and offer places we do cover. */
export function CoverageSuggestions({ place, suggestions, onRephrase }: Props) {
  return (
    <section aria-labelledby="coverage-title" className="px-5 py-[70px] md:px-[8vw] md:py-[110px]">
      <Eyebrow>Couverture Novoya</Eyebrow>
      <h1 id="coverage-title" className="mb-[23px] text-[47px] leading-[0.98] md:text-[clamp(56px,5.6vw,82px)]">
        {place} nous fait rêver aussi.
        <br />
        <em>Mais pas encore.</em>
      </h1>
      <p className="max-w-[680px] leading-[1.7] text-muted">
        Nous n’avons pas encore de partenaire actif pour cette destination. Plutôt que d’inventer, voici
        {suggestions.length > 0
          ? ' des destinations que notre agence peut réellement composer pour vous.'
          : ' notre conseil : reformulez votre envie avec une autre destination.'}
      </p>
      {suggestions.length > 0 && (
        <ul className="my-[45px] grid list-none gap-2.5 p-0 md:grid-cols-3 md:gap-[18px]">
          {suggestions.map((suggestion) => (
            <li key={suggestion.key}>
              <button
                type="button"
                onClick={suggestion.onPick}
                className="group relative grid w-full grid-cols-[115px_1fr] bg-white text-left md:block"
              >
                <img src={suggestion.image} alt="" className="h-[110px] w-full object-cover md:h-[230px]" />
                <span className="grid p-5">
                  <span className="mb-2 text-xs text-muted">Composer ici</span>
                  <strong className="font-serif text-lg font-normal">{suggestion.label}</strong>
                </span>
                <span
                  aria-hidden="true"
                  className="absolute right-5 bottom-[25px] transition-transform group-hover:translate-x-1"
                >
                  →
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <Button variant="link" size="inline" className="min-h-11" onClick={onRephrase}>
        ← Reformuler mon envie
      </Button>
    </section>
  )
}
