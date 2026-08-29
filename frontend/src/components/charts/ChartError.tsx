export function ChartError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      <p className="text-sm text-[var(--loss)]">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="text-xs text-[var(--accent)] hover:underline"
        >
          Retry
        </button>
      )}
    </div>
  );
}
