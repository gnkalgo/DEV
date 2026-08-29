"use client";

import { EMA_COLORS } from "./chartTheme";
import type { ChartSettings } from "@/lib/chartSettings";

export function ChartLegend({ settings }: { settings: ChartSettings }) {
  const items: { label: string; color: string }[] = [];

  if (settings.ema.enabled) {
    settings.ema.periods.forEach((p) => {
      items.push({ label: `EMA ${p}`, color: EMA_COLORS[p] || "#888" });
    });
  }
  if (settings.supertrend.enabled) {
    items.push({
      label: `ST ${settings.supertrend.period},${settings.supertrend.multiplier}`,
      color: "#22c55e",
    });
  }
  if (settings.rsi.enabled) {
    items.push({ label: `RSI ${settings.rsi.period}`, color: "#8b5cf6" });
  }

  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 px-2 py-1 border-b border-[var(--line)]">
      {items.map((item) => (
        <span key={item.label} className="flex items-center gap-1 text-[10px] text-[var(--muted)]">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
          {item.label}
        </span>
      ))}
    </div>
  );
}
