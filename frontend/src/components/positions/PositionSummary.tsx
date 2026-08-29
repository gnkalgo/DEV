"use client";

import { SummaryTile } from "@/components/ui/terminal";
import { fmtINR } from "@/lib/format";
import type { NormalizedPosition } from "@/lib/portfolio";

export function PositionSummary({ positions }: { positions: NormalizedPosition[] }) {
  const open = positions.filter((p) => p.netQty !== 0);
  const totalPnl = open.reduce((s, p) => s + p.totalPnl, 0);
  const realized = open.reduce((s, p) => s + p.realizedPnl, 0);
  const unrealized = open.reduce((s, p) => s + p.unrealizedPnl, 0);
  const dayPnl = unrealized;

  return (
    <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
      <SummaryTile label="Total P&L" value={fmtINR(totalPnl)} pnl={totalPnl} />
      <SummaryTile label="Day P&L" value={fmtINR(dayPnl)} pnl={dayPnl} />
      <SummaryTile label="Realized P&L" value={fmtINR(realized)} pnl={realized} />
      <SummaryTile label="Unrealized P&L" value={fmtINR(unrealized)} pnl={unrealized} />
    </div>
  );
}
