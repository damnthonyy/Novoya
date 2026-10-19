export function Divider({ label }: { label?: string }) {
    return (
      <div role="separator" className="flex items-center gap-4 text-xs text-muted">
        <span className="h-px flex-1 bg-line" />
        {label && <span>{label}</span>}
        <span className="h-px flex-1 bg-line" />
      </div>
    )
  }