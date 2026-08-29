"use client";

import { PnlText } from "@/components/ui/terminal";
import { fmtINR } from "@/lib/format";
import type { NormalizedPosition } from "@/lib/portfolio";

export function PositionsTable({
  positions,
  onExit,
}: {
  positions: NormalizedPosition[];
  onExit: (p: NormalizedPosition) => void;
}) {
  if (!positions.length) {
    return null;
  }

  return (
    <div className="overflow-x-auto">
      <table className="terminal-table w-full min-w-[1000px]">
        <thead>
          <tr className="border-b border-[var(--line)] bg-[var(--panel-2)]">
            {[
              "Symbol", "Exch", "Product", "Net", "Buy Qty", "Buy Avg", "Sell Qty", "Sell Avg",
              "LTP", "Invested", "Realized", "Unrealized", "Total P&L", "P&L %", "Actions",
            ].map((h) => (
              <th key={h} className="px-2 py-1.5 text-left">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr key={p.id} className="border-t border-[var(--line)] hover:bg-[var(--panel-2)]/50">
              <td className="px-2 py-1.5 font-medium text-white">{p.symbol}</td>
              <td className="px-2 py-1.5 text-[var(--muted)]">{p.exchange}</td>
              <td className="px-2 py-1.5">{p.product}</td>
              <td className="px-2 py-1.5 tabular-nums">{p.netQty}</td>
              <td className="px-2 py-1.5 tabular-nums">{p.buyQty}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(p.buyAvg)}</td>
              <td className="px-2 py-1.5 tabular-nums">{p.sellQty}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(p.sellAvg)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(p.ltp)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(p.invested)}</td>
              <td className="px-2 py-1.5"><PnlText value={p.realizedPnl} /></td>
              <td className="px-2 py-1.5"><PnlText value={p.unrealizedPnl} /></td>
              <td className="px-2 py-1.5"><PnlText value={p.totalPnl} /></td>
              <td className="px-2 py-1.5">{p.pnlPct != null ? <PnlText value={p.pnlPct} /> : "—"}</td>
              <td className="px-2 py-1.5">
                {p.netQty !== 0 && (
                  <button
                    type="button"
                    onClick={() => onExit(p)}
                    className="rounded bg-[var(--loss)]/20 px-2 py-0.5 text-[10px] font-semibold text-[var(--loss)] hover:bg-[var(--loss)]/30"
                  >
                    EXIT
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
