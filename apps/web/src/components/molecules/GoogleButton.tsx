type GoogleButtonProps = {
    onClick?: () => void
  }
  
  export function GoogleButton({ onClick }: GoogleButtonProps) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex w-full items-center justify-center gap-3 rounded-full border border-line bg-white px-6 py-3.5 text-base text-ink"
      >
        <span aria-hidden="true">G</span>
        Continuer avec Google
      </button>
    )
  }