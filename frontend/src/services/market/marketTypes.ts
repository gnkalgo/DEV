export type MarketIndex = {
  name: string;
  symbol: string;
  ltp: number;
  change: number;
  change_pct: number;
  is_live?: boolean;
};

export type MarketStatus = {
  status: "open" | "closed" | "pre_open";
  label: string;
  session: string;
};

export type MarketIndicesResponse = {
  indices: MarketIndex[];
  updated_at: string;
  source: string;
  disclaimer?: string;
};
