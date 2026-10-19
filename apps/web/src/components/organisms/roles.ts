export type Role = 'client' | 'agent' | 'admin'

/** The roles, in the order the admin page lists them. Their names are in the `admin` namespace. */
export const ROLES: Role[] = ['client', 'agent', 'admin']
