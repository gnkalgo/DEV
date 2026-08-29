"use client";

import { THEMES } from "@/lib/themes";
import { useTheme } from "@/components/theme/ThemeProvider";

export function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {THEMES.map((t) => {
        const active = theme === t.id;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => setTheme(t.id)}
            className={`rounded border p-3 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] ${
              active
                ? "border-[var(--accent)] bg-[var(--panel-2)]"
                : "border-[var(--line)] hover:border-[var(--accent)]/50"
            }`}
            aria-pressed={active}
          >
            <div className="flex gap-2 mb-2">
              <span
                className="h-8 w-8 rounded border"
                style={{ background: t.preview.background, borderColor: t.preview.surface }}
              />
              <span
                className="h-8 flex-1 rounded"
                style={{ background: t.preview.surface }}
              />
              <span
                className="h-8 w-8 rounded"
                style={{ background: t.preview.accent }}
              />
            </div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">{t.name}</p>
            <p className="mt-0.5 text-[11px] text-[var(--text-secondary)]">{t.description}</p>
            {active && (
              <span className="mt-2 inline-block text-[10px] font-semibold uppercase text-[var(--accent)]">
                Selected
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
