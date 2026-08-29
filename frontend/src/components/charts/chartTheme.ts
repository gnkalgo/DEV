export function cssVar(name: string, fallback = "#111315"): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export function chartColors() {
  return {
    background: cssVar("--panel", "#111315"),
    text: cssVar("--text-primary", "#f5f5f5"),
    grid: cssVar("--line", "#2a2f35"),
    border: cssVar("--line", "#2a2f35"),
    profit: cssVar("--profit", "#22c55e"),
    loss: cssVar("--loss", "#ef4444"),
    accent: cssVar("--accent", "#3b82f6"),
    muted: cssVar("--muted", "#9ca3af"),
  };
}

export const EMA_COLORS: Record<number, string> = {
  9: "#f59e0b",
  20: "#3b82f6",
  50: "#a855f7",
  100: "#14b8a6",
  200: "#ec4899",
};
