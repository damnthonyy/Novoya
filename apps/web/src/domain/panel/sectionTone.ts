/**
 * The colour of a preference panel section (#165), the same on the panel and on the
 * Preferences tab. Panel sections come from the model, so any id gets a tone: the usual
 * ones are fixed so they never share a colour, the others are picked from their id.
 * The colours are the theme tokens --color-section-N and --color-section-N-soft (index.css).
 */
export const SECTION_TONES = 6

export type SectionTone = 1 | 2 | 3 | 4 | 5 | 6

const KNOWN: Record<string, SectionTone> = {
  style: 1,
  rhythm: 2,
  pace: 2,
  food: 3,
  stay: 4,
  accommodation: 4,
  activities: 5,
  preferences: 6,
}

export function sectionTone(sectionId: string): SectionTone {
  const id = sectionId.trim().toLowerCase()
  const known = KNOWN[id]
  if (known) return known
  let hash = 0
  for (const char of id) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return ((hash % SECTION_TONES) + 1) as SectionTone
}

/** Literal class names, so Tailwind finds them. */
export const TONE_CLASSES: Record<SectionTone, { accent: string; soft: string }> = {
  1: { accent: 'border-section-1', soft: 'bg-section-1-soft' },
  2: { accent: 'border-section-2', soft: 'bg-section-2-soft' },
  3: { accent: 'border-section-3', soft: 'bg-section-3-soft' },
  4: { accent: 'border-section-4', soft: 'bg-section-4-soft' },
  5: { accent: 'border-section-5', soft: 'bg-section-5-soft' },
  6: { accent: 'border-section-6', soft: 'bg-section-6-soft' },
}
