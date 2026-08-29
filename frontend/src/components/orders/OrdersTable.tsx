"use client";

import { OrderRow } from "@/components/orders/OrderRow";
import type { UnifiedOrder } from "@/lib/orders";
import { EmptyState } from "@/components/ui/terminal";

export function OrdersTable({
  orders,
  onView,
  onRepeat,
}: {
  orders: UnifiedOrder[];
  onView: (o: UnifiedOrder) => void;
  onRepeat: (o: UnifiedOrder) => void;
}) {
  if (!orders.length) {
    return <EmptyState title="No orders" detail="Place a paper order or connect Dhan to sync broker orders." />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="terminal-table w-full min-w-[1100px]">
        <thead>
          <tr className="border-b border-[var(--line)] bg-[var(--panel-2)]">
            {[
              "Symbol", "Exch", "Side", "Product", "Type", "Qty", "Filled", "Price", "Trigger", "Avg", "LTP",
              "Status", "Time", "Broker", "ID", "Actions",
            ].map((h) => (
              <th key={h} className="px-2 py-1.5 text-left">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <OrderRow key={`${o.source}-${o.id}`} order={o} onView={onView} onRepeat={onRepeat} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
