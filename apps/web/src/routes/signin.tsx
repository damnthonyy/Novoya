import { createFileRoute } from '@tanstack/react-router'
import { SignIn } from '../components/SignIn'

export const Route = createFileRoute('/signin')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <section>
      <h1>Connexion à Novoya</h1>
      <SignIn />
    </section>
  )
  
}
