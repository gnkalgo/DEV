export type ThemeId =
  | "light"
  | "background-1"
  | "carbon-black"
  | "royal-blue"
  | "dark-5-1";

export type ThemeDefinition = {
  id: ThemeId;
  name: string;
  description: string;
  preview: { background: string; surface: string; accent: string; text: string };
};

export const THEMES: ThemeDefinition[] = [
  {
    id: "light",
    name: "Light",
    description: "Clean white brokerage interface",
    preview: { background: "#f5f7fa", surface: "#ffffff", accent: "#16a34a", text: "#111827" },
  },
  {
    id: "background-1",
    name: "Background 1",
    description: "Default GnKAlgo brand look",
    preview: { background: "#0d0f10", surface: "#111315", accent: "#2ee6a6", text: "#e4e8eb" },
  },
  {
    id: "carbon-black",
    name: "Carbon Black",
    description: "Institutional carbon terminal",
    preview: { background: "#0a0a0a", surface: "#141414", accent: "#22c55e", text: "#f3f4f6" },
  },
  {
    id: "royal-blue",
    name: "Royal Blue",
    description: "Premium navy financial terminal",
    preview: { background: "#0b1a3a", surface: "#122a52", accent: "#3b82f6", text: "#f8fafc" },
  },
  {
    id: "dark-5-1",
    name: "Dark 5.1",
    description: "Compact dark trading terminal",
    preview: { background: "#080808", surface: "#121212", accent: "#2ee6a6", text: "#e5e7eb" },
  },
];

export const THEME_STORAGE_KEY = "gnk_theme";
export const DEFAULT_THEME: ThemeId = "background-1";

export const THEME_CSS: Record<ThemeId, Record<string, string>> = {
  light: {
    "--background": "#f5f7fa",
    "--foreground": "#111827",
    "--panel": "#ffffff",
    "--panel-2": "#f0f2f5",
    "--line": "#e2e8f0",
    "--line-soft": "#edf2f7",
    "--accent": "#16a34a",
    "--accent-2": "#2563eb",
    "--danger": "#dc2626",
    "--profit": "#16a34a",
    "--loss": "#dc2626",
    "--muted": "#64748b",
    "--surface": "#ffffff",
    "--surface-secondary": "#f0f2f5",
    "--border": "#e2e8f0",
    "--text-primary": "#111827",
    "--text-secondary": "#64748b",
    "--positive": "#16a34a",
    "--negative": "#dc2626",
    "--warning": "#d97706",
  },
  "background-1": {
    "--background": "#0d0f10",
    "--foreground": "#e4e8eb",
    "--panel": "#111315",
    "--panel-2": "#161a1d",
    "--line": "#252a2e",
    "--line-soft": "#1a1d20",
    "--accent": "#2ee6a6",
    "--accent-2": "#3aa0ff",
    "--danger": "#ff4d4f",
    "--profit": "#22c55e",
    "--loss": "#ef4444",
    "--muted": "#8b949a",
    "--surface": "#111315",
    "--surface-secondary": "#161a1d",
    "--border": "#252a2e",
    "--text-primary": "#e4e8eb",
    "--text-secondary": "#8b949a",
    "--positive": "#22c55e",
    "--negative": "#ef4444",
    "--warning": "#f59e0b",
  },
  "carbon-black": {
    "--background": "#0a0a0a",
    "--foreground": "#f3f4f6",
    "--panel": "#141414",
    "--panel-2": "#1c1c1c",
    "--line": "#2a2a2a",
    "--line-soft": "#1f1f1f",
    "--accent": "#22c55e",
    "--accent-2": "#60a5fa",
    "--danger": "#ef4444",
    "--profit": "#22c55e",
    "--loss": "#ef4444",
    "--muted": "#9ca3af",
    "--surface": "#141414",
    "--surface-secondary": "#1c1c1c",
    "--border": "#2a2a2a",
    "--text-primary": "#f3f4f6",
    "--text-secondary": "#9ca3af",
    "--positive": "#22c55e",
    "--negative": "#ef4444",
    "--warning": "#f59e0b",
  },
  "royal-blue": {
    "--background": "#0b1a3a",
    "--foreground": "#f8fafc",
    "--panel": "#122a52",
    "--panel-2": "#163566",
    "--line": "#1e4078",
    "--line-soft": "#15325c",
    "--accent": "#3b82f6",
    "--accent-2": "#60a5fa",
    "--danger": "#f87171",
    "--profit": "#34d399",
    "--loss": "#f87171",
    "--muted": "#94a3b8",
    "--surface": "#122a52",
    "--surface-secondary": "#163566",
    "--border": "#1e4078",
    "--text-primary": "#f8fafc",
    "--text-secondary": "#94a3b8",
    "--positive": "#34d399",
    "--negative": "#f87171",
    "--warning": "#fbbf24",
  },
  "dark-5-1": {
    "--background": "#080808",
    "--foreground": "#e5e7eb",
    "--panel": "#121212",
    "--panel-2": "#181818",
    "--line": "#262626",
    "--line-soft": "#1a1a1a",
    "--accent": "#2ee6a6",
    "--accent-2": "#38bdf8",
    "--danger": "#ef4444",
    "--profit": "#22c55e",
    "--loss": "#ef4444",
    "--muted": "#a1a1aa",
    "--surface": "#121212",
    "--surface-secondary": "#181818",
    "--border": "#262626",
    "--text-primary": "#e5e7eb",
    "--text-secondary": "#a1a1aa",
    "--positive": "#22c55e",
    "--negative": "#ef4444",
    "--warning": "#f59e0b",
  },
};

export function applyTheme(themeId: ThemeId) {
  const vars = THEME_CSS[themeId] || THEME_CSS[DEFAULT_THEME];
  const root = document.documentElement;
  root.setAttribute("data-theme", themeId);
  Object.entries(vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
}

export function getStoredTheme(): ThemeId {
  if (typeof window === "undefined") return DEFAULT_THEME;
  const stored = localStorage.getItem(THEME_STORAGE_KEY) as ThemeId | null;
  if (stored && THEME_CSS[stored]) return stored;
  return DEFAULT_THEME;
}
