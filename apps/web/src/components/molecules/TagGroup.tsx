import { useTranslation } from 'react-i18next'

import { sectionTone, TONE_CLASSES } from '../../domain/panel/sectionTone'
import { TagToggle } from './TagToggle'

type Props = {
  title: string
  /** Several tags can be picked; otherwise one at most. */
  multi: boolean
  tags: { id: string; label: string }[]
  selected: string[]
  onToggle: (tagId: string) => void
  /** The section's id: its colour is the same as on the Preferences tab. */
  sectionId?: string
}

/** One section of the preferences panel: a title and its tags. */
export function TagGroup({ title, multi, tags, selected, onToggle, sectionId }: Props) {
  const { t } = useTranslation('preferences')
  const tone = sectionId ? sectionTone(sectionId) : undefined
  return (
    <fieldset data-tone={tone} className="m-0 border-0 border-t border-line px-0 py-[25px]">
      <legend
        className={`float-left mb-4 w-full p-0 font-serif text-lg ${tone ? `border-l-4 pl-3 ${TONE_CLASSES[tone].accent}` : ''}`}
      >
        {title}
        {!multi && <span className="ml-2 font-sans text-xs text-muted">{t('singleChoice')}</span>}
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
