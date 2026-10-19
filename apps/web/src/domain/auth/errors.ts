// The codes the API puts in /login?error=<code> when a Google sign-in fails.
const MESSAGES: Record<string, string> = {
  oauth_cancelled: 'Vous avez annulé la connexion avec Google.',
  oauth_failed: 'La connexion avec Google n’a pas fonctionné. Réessayez.',
  oauth_state_invalid:
    'La connexion a pris trop de temps ou a commencé dans un autre navigateur. Réessayez.',
  oauth_email_not_verified: 'Votre adresse Google n’est pas encore vérifiée.',
  oauth_link_not_allowed: 'Ce compte Google ne peut pas être lié à votre compte Novoya.',
  identity_already_linked: 'Ce compte Google est déjà lié à un autre compte Novoya.',
  account_disabled: 'Ce compte est désactivé.',
  user_not_found: 'Nous ne retrouvons pas votre compte. Connectez-vous à nouveau.',
  too_many_attempts: 'Trop de tentatives. Patientez un instant avant de réessayer.',
  unknown_provider: 'La connexion avec Google n’est pas disponible pour le moment.',
}

const FALLBACK = 'Un problème est survenu pendant la connexion. Réessayez.'

/** The message to show for a sign-in error code, or null when there is no error. */
export function signInErrorMessage(code: string | undefined): string | null {
  if (!code) return null
  return MESSAGES[code] ?? FALLBACK
}

// The codes POST /auth/login answers with when an e-mail and password sign-in fails.
const PASSWORD_MESSAGES: Record<string, string> = {
  invalid_credentials: 'E-mail ou mot de passe incorrect.',
  email_not_verified:
    'Confirmez d’abord votre adresse e-mail : ouvrez le lien que nous vous avons envoyé.',
  no_password_set: 'Ce compte se connecte avec Google. Utilisez le bouton « Continuer avec Google ».',
  account_disabled: MESSAGES.account_disabled!,
  too_many_attempts: MESSAGES.too_many_attempts!,
  too_many_requests: MESSAGES.too_many_attempts!,
}

/** The message for a failed e-mail and password sign-in. */
export function passwordSignInErrorMessage(code: string | undefined): string {
  return (code && PASSWORD_MESSAGES[code]) || FALLBACK
}
