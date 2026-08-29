"use client";

import { PnlText } from "@/components/ui/terminal";
import { fmtINR } from "@/lib/format";
import type { NormalizedHolding } from "@/lib/holdings";

export function HoldingsTable({ items }: { items: NormalizedHolding[] }) {
  if (!items.length) return null;

  return (
    <div className="overflow-x-auto">
      <table className="terminal-table w-full min-w-[900px]">
        <thead>
          <tr className="border-b border-[var(--line)] bg-[var(--panel-2)]">
            {[
              "Symbol", "Qty", "Avail", "Avg Cost", "LTP", "Current", "Invested",
              "Day Chg", "Day P&L", "Total P&L", "Returns %",
            ].map((h) => (
              <th key={h} className="px-2 py-1.5 text-left">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((h) => (
            <tr key={h.id} className="border-t border-[var(--line)] hover:bg-[var(--panel-2)]/50">
              <td className="px-2 py-1.5 font-medium text-white">{h.symbol}</td>
              <td className="px-2 py-1.5 tabular-nums">{h.quantity}</td>
              <td className="px-2 py-1.5 tabular-nums">{h.availableQty}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(h.avgCost)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(h.ltp)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(h.currentValue)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(h.investmentValue)}</td>
              <td className="px-2 py-1.5 tabular-nums">{fmtINR(h.dayChange)}</td>
              <td className="px-2 py-1.5"><PnlText value={h.dayPnl ?? 0} /></td>
              <td className="px-2 py-1.5"><PnlText value={h.totalPnl ?? 0} /></td>
              <td className="px-2 py-1.5">
                {h.returnsPct != null ? <PnlText value={h.returnsPct} /> : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
