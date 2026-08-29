"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import {
  applyTheme,
  DEFAULT_THEME,
  getStoredTheme,
  THEME_STORAGE_KEY,
  type ThemeId,
} from "@/lib/themes";

type ThemeContextValue = {
  theme: ThemeId;
  setTheme: (id: ThemeId, persistRemote?: boolean) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>(() =>
    typeof window !== "undefined" ? getStoredTheme() : DEFAULT_THEME,
  );

  useEffect(() => {
    applyTheme(getStoredTheme());
    api<{ theme_preference?: string }>("/api/v1/profile/", {}, true)
      .then((p) => {
        const remote = p.theme_preference as ThemeId | undefined;
        if (remote) {
          setThemeState(remote);
          applyTheme(remote);
          localStorage.setItem(THEME_STORAGE_KEY, remote);
        }
      })
      .catch(() => undefined);
  }, []);

  const setTheme = useCallback((id: ThemeId, persistRemote = true) => {
    setThemeState(id);
    applyTheme(id);
    localStorage.setItem(THEME_STORAGE_KEY, id);
    if (persistRemote) {
      api("/api/v1/profile/", {
        method: "PATCH",
        body: JSON.stringify({ theme_preference: id }),
      }, true).catch(() => undefined);
    }
  }, []);

  const value = useMemo(() => ({ theme, setTheme }), [theme, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
