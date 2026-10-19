import { TagToggle } from './TagToggle'

type Props = {
  title: string
  /** Several tags can be picked; otherwise one at most. */
  multi: boolean
  tags: { id: string; label: string }[]
  selected: string[]
  onToggle: (tagId: string) => void
}

/** One section of the preferences panel: a title and its tags. */
export function TagGroup({ title, multi, tags, selected, onToggle }: Props) {
  return (
    <fieldset className="m-0 border-0 border-t border-line px-0 py-[25px]">
      <legend className="float-left mb-4 w-full p-0 font-serif text-lg">
        {title}
        {!multi && <span className="ml-2 font-sans text-xs text-muted">un seul choix</span>}
      </legend>
      <div className="clear-both flex flex-wrap gap-2.5">
        {tags.map((tag) => (
          <TagToggle
            key={tag.id}
            label={tag.label}
            selected={selected.includes(tag.id)}
            onToggle={() => onToggle(tag.id)}
          />
        ))}
      </div>
    </fieldset>
  )
}
