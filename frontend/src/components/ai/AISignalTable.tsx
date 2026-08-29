"use client";

type Signal = {
  id: string;
  symbol: string;
  action: string;
  confidence: number;
  price?: number | null;
  created_at: string;
};

function signalColor(action: string) {
  const a = action.toUpperCase();
  if (a.includes("STRONG BUY") || a === "BUY") return "text-[var(--profit)]";
  if (a.includes("STRONG SELL") || a === "SELL") return "text-[var(--loss)]";
  return "text-[var(--muted)]";
}

export function AISignalTable({ items }: { items: Signal[] }) {
  if (!items.length) return null;

  return (
    <div className="overflow-x-auto">
      <table className="terminal-table w-full">
        <thead>
          <tr className="border-b border-[var(--line)] bg-[var(--panel-2)]">
            {["Symbol", "Signal", "Confidence", "Entry", "Current", "Generated"].map((h) => (
              <th key={h} className="px-2 py-1.5 text-left">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((s) => (
            <tr key={s.id} className="border-t border-[var(--line)]">
              <td className="px-2 py-1.5 font-medium text-white">{s.symbol}</td>
              <td className={`px-2 py-1.5 font-semibold ${signalColor(s.action)}`}>{s.action}</td>
              <td className="px-2 py-1.5 tabular-nums">{(s.confidence * 100).toFixed(0)}%</td>
              <td className="px-2 py-1.5 tabular-nums">{s.price ?? "—"}</td>
              <td className="px-2 py-1.5 tabular-nums">{s.price ?? "—"}</td>
              <td className="px-2 py-1.5 text-[var(--muted)]">
                {new Date(s.created_at).toLocaleString("en-IN", { dateStyle: "short", timeStyle: "short" })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
