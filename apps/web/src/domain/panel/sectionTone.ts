/**
 * The colours of the preference panel sections (#165), on the panel and on the Preferences
 * tab. Panel sections come from the model, so any id gets a tone:
 * - the usual sections have fixed tones, so they look the same on every page;
 * - the other sections of the same page take the tones still unused, in the order given,
 *   so up to 6 sections on one page never share a colour. Past 6, a tone is picked from the id.
 * The same list of sections always gets the same tones.
 * The colours are the theme tokens --color-section-N and --color-section-N-soft (index.css).
 */
export const SECTION_TONES = 6

export type SectionTone = 1 | 2 | 3 | 4 | 5 | 6

const ALL_TONES: SectionTone[] = [1, 2, 3, 4, 5, 6]

// A Map, not an object: a section named "constructor" must not reach Object.prototype.
const KNOWN = new Map<string, SectionTone>([
  ['style', 1],
  ['rhythm', 2],
  ['pace', 2],
  ['food', 3],
  ['stay', 4],
  ['accommodation', 4],
  ['activities', 5],
  ['preferences', 6],
])

const key = (sectionId: string) => sectionId.trim().toLowerCase()

/** The tone of each section shown together on one page, keyed by section id. */
export function sectionTones(sectionIds: readonly string[]): Map<string, SectionTone> {
  const tones = new Map<string, SectionTone>()
  const used = new Set<SectionTone>()
  for (const id of sectionIds) {
    const known = KNOWN.get(key(id))
    if (known) {
      tones.set(id, known)
      used.add(known)
    }
  }
  for (const id of sectionIds) {
    if (tones.has(id)) continue
    const free = ALL_TONES.find((tone) => !used.has(tone))
    const tone = free ?? hashTone(key(id))
    tones.set(id, tone)
    used.add(tone)
  }
  return tones
}

function hashTone(id: string): SectionTone {
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
