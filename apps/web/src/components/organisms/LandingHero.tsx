import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import { Photo } from '../atoms/Photo'
import { Eyebrow } from '../atoms/Eyebrow'
import { PublicHeader } from './PublicHeader'

type Props = {
  image: string
  imageAlt: string
  signedIn: boolean
  /** The calls to action under the copy. */
  actions: ReactNode
}

/** The landing page's first screen: full-height photo, header, promise and actions. */
export function LandingHero({ image, imageAlt, signedIn, actions }: Props) {
  const { t } = useTranslation('home')
  return (
    <section className="relative h-[760px] overflow-hidden text-white md:h-screen md:min-h-[700px]">
      <Photo src={image} alt={imageAlt} fetchPriority="high" className="absolute inset-0 size-full animate-zoom object-cover" />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[rgb(13_35_31/0.5)] md:bg-[linear-gradient(90deg,rgb(13_35_31/0.8)_0%,rgb(13_35_31/0.45)_54%,rgb(13_35_31/0.25))]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(0deg,rgb(10_28_25/0.75),transparent_45%),linear-gradient(180deg,rgb(10_28_25/0.6),transparent_22%)]"
      />
      <PublicHeader signedIn={signedIn} />
      <div className="absolute inset-x-6 top-[49%] -translate-y-1/2 md:right-auto md:left-[8.3vw] md:top-[51%] md:max-w-[790px]">
        <div className="animate-reveal">
          <Eyebrow light>{t('heroEyebrow')}</Eyebrow>
          <h1 className="mb-[30px] text-[56px] leading-[0.91] md:text-[clamp(70px,7.2vw,116px)]">
            {t('titleStart')}
            <br />
            <em className="text-[0.78em]">{t('titleEnd')}</em>
          </h1>
          <p className="mb-[34px] max-w-[570px] text-sm leading-normal text-white/85 md:text-[17px] md:leading-[1.65]">
            {t('heroIntro')}
          </p>
          <div className="grid gap-2.5 md:flex">{actions}</div>
        </div>
      </div>
      <div
        aria-hidden="true"
        className="absolute inset-x-6 bottom-[30px] flex items-center gap-3.5 text-xs tracking-[0.15em] uppercase md:inset-x-[5vw]"
      >
        <span>01</span>
        <span className="h-px w-[65px] bg-white/60" />
        <span className="ml-auto">{t('heroFoot')}</span>
      </div>
    </section>
  )
}
