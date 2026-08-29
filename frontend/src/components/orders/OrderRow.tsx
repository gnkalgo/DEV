"use client";

import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { fmtINR, fmtTime } from "@/lib/format";
import type { UnifiedOrder } from "@/lib/orders";

export function OrderRow({
  order,
  onView,
  onRepeat,
}: {
  order: UnifiedOrder;
  onView: (o: UnifiedOrder) => void;
  onRepeat: (o: UnifiedOrder) => void;
}) {
  const sideColor = order.side === "BUY" ? "text-[var(--profit)]" : "text-[var(--loss)]";

  return (
    <tr className="border-t border-[var(--line)] hover:bg-[var(--panel-2)]/50">
      <td className="px-2 py-1.5 font-medium text-white">{order.symbol}</td>
      <td className="px-2 py-1.5 text-[var(--muted)]">{order.exchange}</td>
      <td className={`px-2 py-1.5 font-semibold ${sideColor}`}>{order.side}</td>
      <td className="px-2 py-1.5">{order.product}</td>
      <td className="px-2 py-1.5">{order.orderType}</td>
      <td className="px-2 py-1.5 tabular-nums">{order.quantity}</td>
      <td className="px-2 py-1.5 tabular-nums">{order.filledQty}</td>
      <td className="px-2 py-1.5 tabular-nums">{fmtINR(order.price)}</td>
      <td className="px-2 py-1.5 tabular-nums">{fmtINR(order.triggerPrice)}</td>
      <td className="px-2 py-1.5 tabular-nums">{fmtINR(order.avgPrice)}</td>
      <td className="px-2 py-1.5 tabular-nums">{fmtINR(order.ltp)}</td>
      <td className="px-2 py-1.5"><OrderStatusBadge status={order.status} /></td>
      <td className="px-2 py-1.5 text-[var(--muted)]">{fmtTime(order.orderTime)}</td>
      <td className="px-2 py-1.5 text-[var(--muted)]">{order.broker}</td>
      <td className="px-2 py-1.5 text-[10px] text-[var(--muted)] max-w-[80px] truncate">{order.orderId}</td>
      <td className="px-2 py-1.5">
        <div className="flex gap-1">
          <button type="button" onClick={() => onView(order)} className="rounded border border-[var(--line)] px-1.5 py-0.5 text-[10px] hover:bg-[var(--panel-2)]">
            Details
          </button>
          <button type="button" onClick={() => onRepeat(order)} className="rounded border border-[var(--line)] px-1.5 py-0.5 text-[10px] hover:bg-[var(--panel-2)]">
            Repeat
          </button>
        </div>
      </td>
    </tr>
  );
}
