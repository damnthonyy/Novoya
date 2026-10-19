import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'quiet'

export function Button({
  variant = 'primary',
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type="button" className={classes(variant, className)} {...props} />
}

/** A link that looks like a button, for actions that leave the app (e.g. signing in with Google). */
export function ButtonLink({
  variant = 'primary',
  className,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement> & { variant?: Variant }) {
  return <a className={classes(variant, className)} {...props} />
}

function classes(variant: Variant, className?: string) {
  return ['button', `button--${variant}`, className].filter(Boolean).join(' ')
}
