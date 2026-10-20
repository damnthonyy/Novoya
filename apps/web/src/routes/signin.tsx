import { createFileRoute } from '@tanstack/react-router'

import { SignInForm } from '../components/organisms/SignInForm'
import { AuthTemplate } from '../components/templates/AuthTemplate'

export const Route = createFileRoute('/signin')({
  component: SignInPage,
})

function SignInPage() {
  return (
    <AuthTemplate
      media={<div className="flex h-full items-end bg-ink p-12 text-white">Photo : mer Égée · Grèce</div>}
    >
      <p className="text-xs uppercase tracking-widest text-muted">Heureux de vous revoir</p>
      <h1 className="title">Se connecter</h1>
      <p className="text-muted">
        Retrouvez vos envies, vos aperçus et toutes vos conversations.
      </p>

      <SignInForm
        // À remplacer par le client d’API généré quand #61 sera prête
        onSubmit={async (values) => console.log(values.email)}
        onGoogle={() => console.log('google sign-in')}
      />

      <p className="text-xs text-muted">
        En continuant, vous acceptez nos conditions et notre politique de confidentialité.
      </p>
    </AuthTemplate>
  )
}