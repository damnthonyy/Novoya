import type { ReactNode } from 'react'

type Props = {
  /** The photo side (AuthMedia). On phones, a band above the form. */
  media: ReactNode
  children: ReactNode
}

/** The account pages: a photo, then the form in a narrow column. */
export function AuthTemplate({ media, children }: Props) {
  return (
    <main className="min-h-screen md:grid md:h-screen md:grid-cols-[1.05fr_0.95fr]">
      {media}
      <section className="grid place-items-center bg-paper px-[22px] py-[45px] md:overflow-y-auto md:p-[30px]">
        <div className="w-full max-w-[420px]">{children}</div>
      </section>
    </main>
  )
}
