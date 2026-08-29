"use client";

import type { UnifiedOrder } from "@/lib/orders";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { StatRow } from "@/components/ui/terminal";
import { fmtINR, fmtTime } from "@/lib/format";

export function OrderDetailsDrawer({
  order,
  onClose,
}: {
  order: UnifiedOrder | null;
  onClose: () => void;
}) {
  if (!order) return null;

  const remaining = order.quantity - order.filledQty;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-md border-l border-[var(--line)] bg-[var(--panel)] p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Order Details</h2>
          <button type="button" onClick={onClose} className="text-[var(--muted)] hover:text-white">✕</button>
        </div>
        <div className="mt-4 space-y-1">
          <StatRow label="Order ID" value={order.orderId} />
          <StatRow label="Broker Order ID" value={order.brokerOrderId || "—"} />
          <StatRow label="Symbol" value={order.symbol} />
          <StatRow label="Exchange" value={order.exchange} />
          <StatRow label="Transaction" value={order.side} />
          <StatRow label="Product" value={order.product} />
          <StatRow label="Order Type" value={order.orderType} />
          <StatRow label="Quantity" value={order.quantity} />
          <StatRow label="Filled Qty" value={order.filledQty} />
          <StatRow label="Remaining Qty" value={remaining} />
          <StatRow label="Price" value={fmtINR(order.price)} />
          <StatRow label="Trigger Price" value={fmtINR(order.triggerPrice)} />
          <StatRow label="Average Price" value={fmtINR(order.avgPrice)} />
          <StatRow label="Status" value={<OrderStatusBadge status={order.status} />} />
          <StatRow label="Created" value={fmtTime(order.orderTime)} />
          <StatRow label="Broker" value={order.broker} />
          {order.message && <StatRow label="Rejection / Note" value={order.message} />}
        </div>
      </div>
    </div>
  );
}
