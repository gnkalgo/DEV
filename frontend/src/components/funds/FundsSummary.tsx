"use client";

import { SummaryTile } from "@/components/ui/terminal";
import { fmtINR, pickNum } from "@/lib/format";

export function FundsSummaryCard({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return null;

  const available = pickNum(data, [
    "availableBalance", "availabelBalance", "available_balance", "sodLimit",
  ]);
  const margin = pickNum(data, ["utilizedAmount", "usedMargin", "utilized_margin"]);
  const opening = pickNum(data, ["sodLimit", "openingBalance"]);
  const collateral = pickNum(data, ["collateralAmount", "collateral"]);
  const withdrawable = pickNum(data, ["withdrawableBalance", "withdrawable_balance"]);
  const unsettled = pickNum(data, ["receiveableAmount", "unsettledCredits"]);

  return (
    <div className="grid grid-cols-2 gap-2 lg:grid-cols-3">
      <SummaryTile label="Available Balance" value={fmtINR(available)} />
      <SummaryTile label="Used Margin" value={fmtINR(margin)} />
      <SummaryTile label="Opening Balance" value={fmtINR(opening)} />
      <SummaryTile label="Collateral" value={fmtINR(collateral)} />
      <SummaryTile label="Withdrawable" value={fmtINR(withdrawable)} />
      <SummaryTile label="Unsettled Credits" value={fmtINR(unsettled)} />
    </div>
  );
}

export function MarginBreakdown({ data }: { data: Record<string, unknown> | null }) {
  if (!data) return null;

  const rows: { label: string; keys: string[] }[] = [
    { label: "Available Cash", keys: ["availableBalance", "availabelBalance"] },
    { label: "Used Margin", keys: ["utilizedAmount", "usedMargin"] },
    { label: "Collateral", keys: ["collateralAmount", "collateral"] },
    { label: "Option Premium", keys: ["optionPremium", "option_premium"] },
    { label: "Exposure Margin", keys: ["exposureMargin", "exposure_margin"] },
    { label: "SPAN Margin", keys: ["spanMargin", "span_margin"] },
    { label: "Delivery Margin", keys: ["deliveryMargin", "delivery_margin"] },
  ];

  const visible = rows.filter((r) => pickNum(data, r.keys) != null);
  if (!visible.length) return null;

  return (
    <div className="rounded border border-[var(--line)] bg-[var(--panel-2)] p-3">
      <h3 className="text-[10px] font-semibold uppercase tracking-wide text-[var(--muted)]">Fund Usage</h3>
      <div className="mt-2 space-y-1">
        {visible.map((r) => (
          <div key={r.label} className="flex justify-between text-xs">
            <span className="text-[var(--muted)]">{r.label}</span>
            <span className="tabular-nums text-white">{fmtINR(pickNum(data, r.keys))}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
