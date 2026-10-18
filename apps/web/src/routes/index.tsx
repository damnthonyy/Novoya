import { createFileRoute } from '@tanstack/react-router'

import { ApiStatus } from '../components/ApiStatus'
import { WishForm } from '../components/wishForm'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <section>
      <h1>Plan your next trip</h1>
      <p>Tell us what you want and we build the trip around it.</p>
      <WishForm  />
      <ApiStatus />
    </section>
  )
}
