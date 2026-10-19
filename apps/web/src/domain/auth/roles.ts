export type Role = 'client' | 'agent' | 'admin'

/** The back-office areas and who may open them. Same rule as the API's role checks. */
const AREAS = {
  agent: ['agent', 'admin'],
  admin: ['admin'],
} satisfies Record<string, Role[]>

export function canOpen(role: Role, area: keyof typeof AREAS): boolean {
  return (AREAS[area] as Role[]).includes(role)
}
