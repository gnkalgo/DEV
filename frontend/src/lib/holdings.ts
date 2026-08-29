"use client";

import { pickNum, pickStr } from "@/lib/format";

export type NormalizedHolding = {
  id: string;
  symbol: string;
  quantity: number;
  availableQty: number;
  avgCost: number | null;
  ltp: number | null;
  currentValue: number | null;
  investmentValue: number | null;
  dayChange: number | null;
  dayPnl: number | null;
  totalPnl: number | null;
  returnsPct: number | null;
  raw: Record<string, unknown>;
};

export function normalizeHolding(raw: Record<string, unknown>, index: number): NormalizedHolding {
  const symbol = pickStr(raw, ["tradingSymbol", "symbol", "securityId"], `H-${index}`);
  const quantity = pickNum(raw, ["totalQty", "quantity", "holdingQty"]) ?? 0;
  const availableQty = pickNum(raw, ["availableQty", "availableQuantity"]) ?? quantity;
  const avgCost = pickNum(raw, ["avgCostPrice", "averagePrice", "costPrice"]);
  const ltp = pickNum(raw, ["ltp", "lastPrice", "lastTradedPrice"]);
  const currentValue = pickNum(raw, ["currentValue", "marketValue"]) ?? (ltp && quantity ? ltp * quantity : null);
  const investmentValue = pickNum(raw, ["investmentValue", "costValue"]) ?? (avgCost && quantity ? avgCost * quantity : null);
  const dayChange = pickNum(raw, ["dayChange", "change"]);
  const dayPnl = pickNum(raw, ["dayPnl", "dayProfit"]);
  const totalPnl = pickNum(raw, ["pnl", "totalPnl", "profitAndLoss"]) ??
    (currentValue != null && investmentValue != null ? currentValue - investmentValue : null);
  const returnsPct = investmentValue && totalPnl != null && investmentValue > 0
    ? (totalPnl / investmentValue) * 100
    : pickNum(raw, ["returnsPct", "returns"]);

  return {
    id: pickStr(raw, ["id", "securityId"], `${symbol}-${index}`),
    symbol,
    quantity,
    availableQty,
    avgCost,
    ltp,
    currentValue,
    investmentValue,
    dayChange,
    dayPnl,
    totalPnl,
    returnsPct,
    raw,
  };
}
