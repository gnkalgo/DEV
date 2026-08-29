"use client";

import { TIMEFRAMES, type TimeframeId } from "@/lib/chartSettings";

export function TimeframeSelector({
  value,
  onChange,
}: {
  value: TimeframeId;
  onChange: (id: TimeframeId) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-0.5">
      <span className="mb-1 block text-[10px] uppercase text-[var(--muted)] w-full">Timeframe</span>
      {TIMEFRAMES.map((tf) => (
        <button
          key={tf.id}
          type="button"
          onClick={() => onChange(tf.id)}
          className={`rounded px-2 py-1 text-[10px] font-medium tabular-nums transition-colors ${
            value === tf.id
              ? "bg-[var(--accent)] text-black"
              : "border border-[var(--line)] text-[var(--muted)] hover:text-white"
          }`}
        >
          {tf.label}
        </button>
      ))}
    </div>
  );
}
