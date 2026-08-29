"use client";

import { useEffect, useState } from "react";

import type { MarketIndex, MarketStatus } from "@/services/market/marketTypes";
import { marketDataService } from "@/services/market/marketDataService";

function fmtNum(n: number, decimals = 2) {
  return n.toLocaleString("en-IN", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function IndexChip({ item }: { item: MarketIndex }) {
  const up = item.change > 0;
  const down = item.change < 0;
  const color = up ? "text-[var(--profit)]" : down ? "text-[var(--loss)]" : "text-[var(--muted)]";
  const arrow = up ? "▲" : down ? "▼" : "—";

  return (
    <div className="flex shrink-0 items-center gap-2 border-r border-[var(--line)] px-3 py-1.5 last:border-r-0">
      <span className="text-[11px] font-medium text-[var(--muted)] whitespace-nowrap">{item.name}</span>
      <span className="text-xs font-semibold text-white tabular-nums">{fmtNum(item.ltp)}</span>
      <span className={`text-[11px] tabular-nums ${color}`}>
        {arrow} {item.change >= 0 ? "+" : ""}{fmtNum(item.change)} ({item.change_pct >= 0 ? "+" : ""}{fmtNum(item.change_pct)}%)
      </span>
    </div>
  );
}

export function MarketTicker() {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [status, setStatus] = useState<MarketStatus | null>(null);

  useEffect(() => {
    const refresh = () => {
      setIndices(marketDataService.getIndices());
      setStatus(marketDataService.getStatus());
    };
    refresh();
    marketDataService.connect(15000);
    const unsub = marketDataService.subscribe(refresh);
    return () => {
      unsub();
      marketDataService.disconnect();
    };
  }, []);

  const loop = indices.length ? [...indices, ...indices] : [];
  const statusColor =
    status?.status === "open" ? "text-[var(--profit)]" : status?.status === "pre_open" ? "text-[var(--accent-2)]" : "text-[var(--muted)]";

  return (
    <div className="border-b border-[var(--line)] bg-[var(--panel)]">
      <div className="flex h-[var(--ticker-height)] items-center gap-2 px-2">
        <div className={`flex shrink-0 items-center gap-1.5 px-2 text-[11px] font-medium ${statusColor}`}>
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
          {status?.label ?? "Market"}
        </div>
        <div className="ticker-wrap relative flex-1 min-w-0">
          {loop.length ? (
            <div className="ticker-track flex w-max">
              {loop.map((item, i) => (
                <IndexChip key={`${item.symbol}-${i}`} item={item} />
              ))}
            </div>
          ) : (
            <div className="px-3 text-[11px] text-[var(--muted)]">Loading indices…</div>
          )}
        </div>
      </div>
    </div>
  );
}
