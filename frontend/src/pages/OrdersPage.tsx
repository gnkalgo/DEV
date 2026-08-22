import { useEffect, useState } from "react";
import { DataTable } from "../components/DataTable";
import { getDashboard } from "../services/api";
import { playUiSound } from "../utils/sounds";

export function OrdersPage() {
  const [rows, setRows] = useState<string[][]>([]);

  useEffect(() => {
    void getDashboard().then((data) => {
      setRows(
        data.orders.map((row) => [
          row.id,
          row.symbol,
          row.side,
          row.order_type,
          String(row.quantity),
          row.status,
          row.source,
        ]),
      );
    });
  }, []);

  return (
    <section className="card">
      <h1>Orders</h1>
      <p className="muted">PAPER default. Live orders are not enabled. Cancel sound is UI-only until Phase 5.</p>
      <DataTable
        columns={["ID", "Symbol", "Side", "Type", "Qty", "Status", "Source"]}
        rows={rows}
        empty="No orders"
      />
      <div className="inline-actions">
        <button type="button" disabled>
          Place paper order (Phase 5)
        </button>
        <button type="button" className="secondary" onClick={() => playUiSound("cancel")}>
          Simulate cancel tick
        </button>
      </div>
    </section>
  );
}
