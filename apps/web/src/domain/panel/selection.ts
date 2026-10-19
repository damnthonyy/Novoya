type Tag = { id: string; preselected: boolean }
type Section = { id: string; multi: boolean; tags: Tag[] }

/** The tags picked in each section, by id. */
export type Selection = Record<string, string[]>

/** What the panel picks for the client before they touch it. One tag at most in a single-choice section. */
export function initialSelection(sections: Section[]): Selection {
  const selection: Selection = {}
  for (const section of sections) {
    const picked = section.tags.filter((tag) => tag.preselected).map((tag) => tag.id)
    selection[section.id] = section.multi ? picked : picked.slice(0, 1)
  }
  return selection
}

/** Picks or unpicks a tag. In a single-choice section, picking a tag replaces the previous one. */
export function toggleTag(selection: Selection, section: Section, tagId: string): Selection {
  const current = selection[section.id] ?? []
  const next = current.includes(tagId)
    ? current.filter((id) => id !== tagId)
    : section.multi
      ? [...current, tagId]
      : [tagId]
  return { ...selection, [section.id]: next }
}

/** The selection as the API takes it. */
export function selectedTags(selection: Selection): { section: string; tag: string }[] {
  return Object.entries(selection).flatMap(([section, tags]) => tags.map((tag) => ({ section, tag })))
}

/** The panel answers refused by the API, in words for the client. */
export function answerPanelErrorMessage(code: string | undefined): string {
  switch (code) {
    case 'invalid_answers':
    case 'invalid_input':
      return 'Certaines réponses ne conviennent pas. Vérifiez les dates et le budget, puis réessayez.'
    case 'wish_not_found':
      return 'Nous ne retrouvons pas cette envie. Recommencez depuis le début.'
    case 'invalid_transition':
    case 'conflict':
      return 'Vous avez déjà répondu pour cette envie.'
    case 'too_many_requests':
      return 'Trop de demandes d’un coup. Patientez un instant puis réessayez.'
    default:
      return 'Vos préférences n’ont pas pu être envoyées. Réessayez dans un instant.'
  }
}
