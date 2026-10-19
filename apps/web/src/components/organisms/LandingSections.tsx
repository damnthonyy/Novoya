import type { ReactNode } from 'react'

import { Eyebrow } from '../atoms/Eyebrow'
import { Seal } from '../atoms/Seal'

const display = 'm-0 text-[50px] leading-[0.95] md:text-[clamp(60px,7vw,104px)]'

/** "Moins chercher. Mieux partir.": the promise and the honesty pledge. */
export function Manifesto() {
  return (
    <section className="bg-ivory px-6 py-[90px] md:px-[8vw] md:pt-[150px] md:pb-[140px]">
      <Eyebrow>La promesse Novoya</Eyebrow>
      <h2 className={display}>
        Moins chercher.
        <br />
        <em>Mieux partir.</em>
      </h2>
      <div className="mt-[45px] md:mt-[70px] md:ml-[17vw] md:grid md:grid-cols-[1.2fr_1fr] md:gap-[16vw]">
        <p className="font-serif text-[19px] leading-[1.55] md:text-2xl">
          Vous racontez une envie. Notre concierge IA lui donne une première forme. Puis un agent Novoya la
          rend possible, avec attention et discernement.
        </p>
        <div className="mt-[45px] flex items-start gap-6 leading-[1.65] text-muted md:mt-0">
          <Seal className="size-[58px] text-2xl" />
          <p>
            <strong className="text-ink">Notre parti pris : l’honnêteté.</strong>
            <br />
            Nous ne proposons que des destinations où nos partenaires sont actifs. Si nous ne pouvons pas vous
            y emmener, nous vous le dirons.
          </p>
        </div>
      </div>
    </section>
  )
}

/** "Les plus désirés": a heading, then the trip cards given as children. */
export function PopularTrips({ children }: { children: ReactNode }) {
  return (
    <section id="voyages" aria-labelledby="voyages-title" className="bg-paper px-6 py-[90px] md:px-[5vw] md:py-[140px]">
      <div className="mb-[45px] md:mx-[3vw] md:mb-[75px] md:flex md:items-end md:justify-between">
        <div>
          <Eyebrow>Carnet d’inspirations</Eyebrow>
          <h2 id="voyages-title" className="m-0 text-[50px] leading-[0.95] md:text-[78px]">
            Les plus désirés
          </h2>
        </div>
        <p className="mt-5 max-w-[390px] leading-[1.7] text-muted md:mt-0">
          Trois échappées souvent imaginées par nos voyageurs, à réinterpréter selon vos envies.
        </p>
      </div>
      <div className="-mr-6 flex snap-x snap-mandatory gap-5 overflow-x-auto md:mr-0 md:grid md:grid-cols-[1.25fr_0.92fr_0.92fr] md:items-start md:overflow-visible [&>*]:min-w-[84vw] [&>*]:snap-start md:[&>*]:min-w-0">
        {children}
      </div>
    </section>
  )
}

const STEPS = [
  ['01', 'Je décris', 'Une phrase suffit. Vos mots restent chez Novoya.'],
  ['02', 'Je précise', 'Quelques préférences, seulement si vous le souhaitez.'],
  ['03', 'Je découvre', 'Un aperçu jour par jour, toujours modifiable.'],
  ['04', 'J’échange', 'Je l’affine avec le concierge, puis un conseiller prend le relais.'],
] as const

/** "De l’envie au départ.": the four steps, on ink. */
export function Method() {
  return (
    <section
      id="methode"
      className="bg-ink px-6 py-[90px] text-white md:grid md:grid-cols-[0.85fr_1.7fr] md:gap-[10vw] md:px-[8vw] md:py-[145px]"
    >
      <div>
        <Eyebrow light>Une méthode simple</Eyebrow>
        <h2 className="text-[52px] leading-[0.98] md:text-[75px]">
          De l’envie
          <br />
          au départ.
        </h2>
        <p className="max-w-[350px] leading-[1.7] text-white/65">
          La technologie pour clarifier vos envies. L’humain pour négocier, vérifier et prendre soin du reste.
        </p>
      </div>
      <ol className="mt-[55px] list-none p-0 md:mt-0 md:grid md:grid-cols-2">
        {STEPS.map(([number, title, copy]) => (
          <li key={number} className="pt-[15px] pb-[55px] md:pr-10">
            <span className="font-serif text-sm text-coral">{number}</span>
            <div aria-hidden="true" className="mt-[18px] mb-7 h-px bg-white/20" />
            <h3 className="font-serif text-[25px] font-normal">{title}</h3>
            <p className="max-w-[240px] text-[13px] leading-[1.6] text-white/65">{copy}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

const PROMISES = [
  ['01', 'Des offres réelles', 'Chaque proposition correspond à une offre active chez l’un de nos partenaires.'],
  ['02', 'Un aperçu sans prix', 'L’IA compose et ajuste le voyage avec vous, sans jamais inventer de montant.'],
  ['03', 'Vos mots, seulement', 'Jamais d’import d’e-mails ou de réseaux sociaux. Vous gardez le contrôle.'],
] as const

/** "Rien d’inventé. Rien d’intrusif.": three promises. */
export function Trust() {
  return (
    <section className="bg-ivory px-6 py-[90px] md:grid md:grid-cols-[1.1fr_1fr] md:gap-[12vw] md:px-[8vw] md:py-[150px]">
      <div>
        <Eyebrow>Un voyage vrai, dès le premier mot</Eyebrow>
        <h2 className="m-0 text-[50px] leading-[0.95] md:text-[72px]">
          Rien d’inventé.
          <br />
          Rien d’intrusif.
        </h2>
      </div>
      <ul className="mt-[50px] min-w-0 list-none p-0 md:mt-0">
        {PROMISES.map(([number, title, copy]) => (
          <li
            key={number}
            className="grid grid-cols-[30px_1fr] gap-5 border-t border-line py-[27px] lg:grid-cols-[40px_180px_1fr]"
          >
            <span className="font-serif text-coral-text">{number}</span>
            <h3 className="m-0 font-serif text-[21px] font-normal">{title}</h3>
            <p className="col-start-2 m-0 text-[13px] leading-[1.6] text-muted lg:col-start-auto">{copy}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

/** The last call to action over a photo. */
export function Closing({ image, action }: { image: string; action: ReactNode }) {
  return (
    <section className="relative grid h-[600px] place-items-center text-center text-white md:h-[720px]">
      <img src={image} alt="" loading="lazy" className="absolute inset-0 size-full object-cover" />
      <div aria-hidden="true" className="absolute inset-0 bg-[rgb(11_36_31/0.6)]" />
      <div className="relative px-6">
        <Eyebrow light>Votre prochain voyage commence ici</Eyebrow>
        <h2 className="mb-[35px] text-[55px] leading-[0.95] md:text-[90px]">
          Où avez-vous
          <br />
          <em>envie d’être ?</em>
        </h2>
        {action}
      </div>
    </section>
  )
}
