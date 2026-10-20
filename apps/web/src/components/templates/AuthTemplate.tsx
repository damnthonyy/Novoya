import type { ReactNode } from 'react'

type AuthTemplateProps = {
  media: ReactNode
  children: ReactNode
}

export function AuthTemplate({ media, children }: AuthTemplateProps) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden lg:block">{media}</div>
      <main className="flex flex-col justify-center gap-6 px-8 py-12 lg:px-16">
        {children}
      </main>
    </div>
  )
}