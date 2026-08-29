const WATCHLIST_KEY = "gnk_watchlists";

export type WatchlistItem = {
  symbol: string;
  exchange: string;
  display_name?: string;
  security_id?: string;
  exchange_segment?: string;
  segment?: string;
};

export type Watchlists = Record<string, WatchlistItem[]>;

export function loadWatchlists(): Watchlists {
  if (typeof window === "undefined") return { "Watchlist 1": [], "Watchlist 2": [], "Watchlist 3": [] };
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    if (raw) return JSON.parse(raw) as Watchlists;
  } catch {
    /* ignore */
  }
  return { "Watchlist 1": [], "Watchlist 2": [], "Watchlist 3": [] };
}

export function saveWatchlists(data: Watchlists) {
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(data));
}
