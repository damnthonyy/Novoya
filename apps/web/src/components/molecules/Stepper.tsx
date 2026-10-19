type Props = {
  value: number
  min: number
  max: number
  onChange: (value: number) => void
  /** What the number counts, for the buttons' labels ("voyageur"). */
  unit: string
  /** The value in words ("2 voyageurs"). */
  valueText: string
  id?: string
  describedBy?: string
}

/** A number changed with − and + buttons. */
export function Stepper({ value, min, max, onChange, unit, valueText, id, describedBy }: Props) {
  const button = 'size-11 bg-ivory text-lg disabled:opacity-40'
  return (
    <div
      id={id}
      role="group"
      aria-describedby={describedBy}
      className="flex items-center justify-between border border-line bg-white p-2"
    >
      <button
        type="button"
        className={button}
        aria-label={`Un ${unit} de moins`}
        disabled={value <= min}
        onClick={() => onChange(value - 1)}
      >
        −
      </button>
      <output aria-live="polite">{valueText}</output>
      <button
        type="button"
        className={button}
        aria-label={`Un ${unit} de plus`}
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
      >
        +
      </button>
    </div>
  )
}
