export const TIMEFRAMES = [
  { id: "1m", label: "1m", seconds: 60 },
  { id: "3m", label: "3m", seconds: 180 },
  { id: "5m", label: "5m", seconds: 300 },
  { id: "15m", label: "15m", seconds: 900 },
  { id: "30m", label: "30m", seconds: 1800 },
  { id: "1H", label: "1H", seconds: 3600 },
  { id: "4H", label: "4H", seconds: 14400 },
  { id: "1D", label: "1D", seconds: 86400 },
  { id: "1W", label: "1W", seconds: 604800 },
] as const;

export type TimeframeId = typeof TIMEFRAMES[number]["id"];

export type ChartSettings = {
  chartType: "candles" | "line";
  showGrid: boolean;
  showVolume: boolean;
  autoScale: boolean;
  ema: { enabled: boolean; periods: number[] };
  supertrend: { enabled: boolean; period: number; multiplier: number };
  rsi: { enabled: boolean; period: number };
};

export const DEFAULT_CHART_SETTINGS: ChartSettings = {
  chartType: "candles",
  showGrid: true,
  showVolume: true,
  autoScale: true,
  ema: { enabled: true, periods: [9, 20, 50, 200] },
  supertrend: { enabled: false, period: 10, multiplier: 3 },
  rsi: { enabled: true, period: 14 },
};

const KEY = "gnk_chart_settings";

export function loadChartSettings(): ChartSettings {
  if (typeof window === "undefined") return DEFAULT_CHART_SETTINGS;
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULT_CHART_SETTINGS, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return DEFAULT_CHART_SETTINGS;
}

export function saveChartSettings(s: ChartSettings) {
  localStorage.setItem(KEY, JSON.stringify(s));
}
