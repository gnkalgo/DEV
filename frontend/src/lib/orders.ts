import { pickNum, pickStr } from "@/lib/format";

export type LocalOrder = {
  id: string;
  symbol: string;
  exchange: string;
  side: string;
  quantity: number;
  order_type: string;
  product_type: string;
  price: number | null;
  status: string;
  broker: string;
  broker_order_id?: string | null;
  source: string;
  message?: string | null;
  created_at: string;
  updated_at?: string | null;
};

export type UnifiedOrder = {
  id: string;
  symbol: string;
  exchange: string;
  side: string;
  product: string;
  orderType: string;
  quantity: number;
  filledQty: number;
  price: number | null;
  triggerPrice: number | null;
  avgPrice: number | null;
  ltp: number | null;
  status: string;
  orderTime: string;
  broker: string;
  orderId: string;
  brokerOrderId?: string | null;
  message?: string | null;
  source: "local" | "broker";
  raw: Record<string, unknown>;
};

export function localToUnified(o: LocalOrder): UnifiedOrder {
  return {
    id: o.id,
    symbol: o.symbol,
    exchange: o.exchange,
    side: o.side,
    product: o.product_type,
    orderType: o.order_type,
    quantity: o.quantity,
    filledQty: o.status.includes("FILLED") ? o.quantity : 0,
    price: o.price,
    triggerPrice: null,
    avgPrice: o.price,
    ltp: null,
    status: o.status,
    orderTime: o.created_at,
    broker: o.broker,
    orderId: o.id,
    brokerOrderId: o.broker_order_id,
    message: o.message,
    source: "local",
    raw: o as unknown as Record<string, unknown>,
  };
}

export function brokerToUnified(raw: Record<string, unknown>, index: number): UnifiedOrder {
  const qty = pickNum(raw, ["quantity", "tradedQuantity", "qty"]) ?? 0;
  const filled = pickNum(raw, ["tradedQuantity", "filledQty", "filled_quantity"]) ?? 0;
  const orderId = pickStr(raw, ["orderId", "order_id", "id"], `broker-${index}`);

  return {
    id: orderId,
    symbol: pickStr(raw, ["tradingSymbol", "symbol", "securityId"]),
    exchange: pickStr(raw, ["exchangeSegment", "exchange"], "NSE"),
    side: pickStr(raw, ["transactionType", "side"], "—"),
    product: pickStr(raw, ["productType", "product"], "—"),
    orderType: pickStr(raw, ["orderType", "order_type"], "—"),
    quantity: qty,
    filledQty: filled,
    price: pickNum(raw, ["price", "limitPrice"]),
    triggerPrice: pickNum(raw, ["triggerPrice", "trigger_price"]),
    avgPrice: pickNum(raw, ["averageTradedPrice", "average_price", "avgPrice"]),
    ltp: pickNum(raw, ["ltp", "lastPrice"]),
    status: pickStr(raw, ["orderStatus", "status"], "—"),
    orderTime: pickStr(raw, ["createTime", "orderTime", "created_at"], ""),
    broker: "dhan",
    orderId: orderId,
    brokerOrderId: orderId,
    message: pickStr(raw, ["omsErrorDescription", "message"], ""),
    source: "broker",
    raw,
  };
}

export function filterOrdersByTab(orders: UnifiedOrder[], tab: string): UnifiedOrder[] {
  const s = tab.toLowerCase();
  if (s === "all") return orders;
  if (s === "pending") return orders.filter((o) =>
    ["PENDING", "OPEN", "TRIGGER PENDING", "PARTIALLY FILLED"].some((x) =>
      o.status.toUpperCase().includes(x.replace(" ", "")) || o.status.toUpperCase() === x,
    ),
  );
  if (s === "executed") return orders.filter((o) =>
    ["TRADED", "FILLED", "PAPER_FILLED", "COMPLETE"].some((x) => o.status.toUpperCase().includes(x)),
  );
  if (s === "rejected") return orders.filter((o) => o.status.toUpperCase().includes("REJECT"));
  if (s === "cancelled") return orders.filter((o) => o.status.toUpperCase().includes("CANCEL"));
  return orders;
}
