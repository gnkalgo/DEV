"use client";

import { useState } from "react";

import type { ChartSettings } from "@/lib/chartSettings";

export function IndicatorToolbar({
  settings,
  onChange,
}: {
  settings: ChartSettings;
  onChange: (s: ChartSettings) => void;
}) {
  const [open, setOpen] = useState(false);

  const toggleEma = () => {
    onChange({ ...settings, ema: { ...settings.ema, enabled: !settings.ema.enabled } });
  };

  const toggleSupertrend = () => {
    onChange({
      ...settings,
      supertrend: { ...settings.supertrend, enabled: !settings.supertrend.enabled },
    });
  };

  const toggleRsi = () => {
    onChange({ ...settings, rsi: { ...settings.rsi, enabled: !settings.rsi.enabled } });
  };

  const toggleVolume = () => {
    onChange({ ...settings, showVolume: !settings.showVolume });
  };

  return (
    <div className="relative">
      <span className="mb-1 block text-[10px] uppercase text-[var(--muted)]">Indicators</span>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded border border-[var(--line)] px-3 py-1.5 text-[10px] font-medium text-white hover:border-[var(--accent)]"
      >
        Indicators ▾
      </button>
      {open && (
        <div
          className="absolute left-0 top-full z-30 mt-1 min-w-[180px] rounded border border-[var(--line)] bg-[var(--panel)] p-2 shadow-lg"
        >
          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input type="checkbox" checked={settings.ema.enabled} onChange={toggleEma} />
            EMA (9, 20, 50, 200)
          </label>
          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input type="checkbox" checked={settings.supertrend.enabled} onChange={toggleSupertrend} />
            Supertrend
          </label>
          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input type="checkbox" checked={settings.rsi.enabled} onChange={toggleRsi} />
            RSI
          </label>
          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input type="checkbox" checked={settings.showVolume} onChange={toggleVolume} />
            Volume
          </label>
          <p className="mt-2 border-t border-[var(--line)] pt-2 text-[10px] text-[var(--muted)]">
            VWAP, MACD, Bollinger — coming soon
          </p>
        </div>
      )}
    </div>
  );
}
