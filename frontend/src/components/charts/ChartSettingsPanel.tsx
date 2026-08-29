"use client";

import { useState } from "react";

import { TerminalInput, TerminalSelect } from "@/components/ui/terminal";
import type { ChartSettings } from "@/lib/chartSettings";

export function ChartSettingsPanel({
  settings,
  onChange,
}: {
  settings: ChartSettings;
  onChange: (s: ChartSettings) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <span className="mb-1 block text-[10px] uppercase text-[var(--muted)]">Settings</span>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded border border-[var(--line)] px-3 py-1.5 text-[10px] font-medium text-white hover:border-[var(--accent)]"
      >
        Settings
      </button>
      {open && (
        <div
          className="absolute right-0 top-full z-30 mt-1 w-64 rounded border border-[var(--line)] bg-[var(--panel)] p-3 shadow-lg"
        >
          <p className="text-[10px] uppercase text-[var(--muted)] mb-2">Chart Type</p>
          <TerminalSelect
            value={settings.chartType}
            onChange={(e) =>
              onChange({ ...settings, chartType: e.target.value as ChartSettings["chartType"] })
            }
            className="w-full mb-3"
          >
            <option value="candles">Candles</option>
            <option value="line">Line</option>
          </TerminalSelect>

          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input
              type="checkbox"
              checked={settings.showGrid}
              onChange={(e) => onChange({ ...settings, showGrid: e.target.checked })}
            />
            Grid lines
          </label>
          <label className="flex items-center gap-2 py-1 text-xs text-white">
            <input
              type="checkbox"
              checked={settings.autoScale}
              onChange={(e) => onChange({ ...settings, autoScale: e.target.checked })}
            />
            Auto scale
          </label>

          <p className="mt-3 text-[10px] uppercase text-[var(--muted)]">Supertrend</p>
          <div className="mt-1 flex gap-2">
            <TerminalInput
              type="number"
              min={1}
              value={settings.supertrend.period}
              onChange={(e) =>
                onChange({
                  ...settings,
                  supertrend: { ...settings.supertrend, period: Number(e.target.value) || 10 },
                })
              }
              className="w-20"
              placeholder="Period"
            />
            <TerminalInput
              type="number"
              min={0.1}
              step={0.1}
              value={settings.supertrend.multiplier}
              onChange={(e) =>
                onChange({
                  ...settings,
                  supertrend: { ...settings.supertrend, multiplier: Number(e.target.value) || 3 },
                })
              }
              className="w-20"
              placeholder="Mult"
            />
          </div>

          <p className="mt-3 text-[10px] uppercase text-[var(--muted)]">RSI period</p>
          <TerminalInput
            type="number"
            min={2}
            value={settings.rsi.period}
            onChange={(e) =>
              onChange({
                ...settings,
                rsi: { ...settings.rsi, period: Number(e.target.value) || 14 },
              })
            }
            className="mt-1 w-20"
          />

          <button
            type="button"
            className="mt-3 text-xs text-[var(--accent)]"
            onClick={() => setOpen(false)}
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
