import { useEffect, useState } from "react";
import { DataTable } from "../components/DataTable";
import { getDashboard } from "../services/api";

export function PositionsPage() {
  const [rows, setRows] = useState<string[][]>([]);

  useEffect(() => {
    void getDashboard().then((data) => {
      setRows(
        data.positions.map((row) => [
          row.symbol,
          row.exchange,
          String(row.quantity),
          row.average_price,
          row.unrealized_pnl,
        ]),
      );
    });
  }, []);

  return (
    <section className="card">
      <h1>Positions</h1>
      <DataTable
        columns={["Symbol", "Exchange", "Qty", "Avg", "Unrealized P&L"]}
        rows={rows}
        empty="No positions until a connected broker supplies data"
      />
    </section>
  );
}
