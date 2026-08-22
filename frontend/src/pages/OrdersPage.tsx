import { useEffect, useState } from "react";
import { DataTable } from "../components/DataTable";
import { cancelOrder, listBrokers, listOrders, placeOrder } from "../services/api";
import { playUiSound } from "../utils/sounds";

export function OrdersPage() {
  const [rows, setRows] = useState<string[][]>([]);
  const [brokerAccountId, setBrokerAccountId] = useState("");
  const [symbol, setSymbol] = useState("NIFTY");
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const orders = await listOrders();
    setRows(
      orders.map((row) => [
        row.id,
        row.symbol,
        row.side,
        row.order_type,
        String(row.quantity),
        row.status,
        row.source,
      ]),
    );
  };

  useEffect(() => {
    void Promise.all([
      listBrokers().then((brokers) => {
        const connected = brokers.find((row) => row.status === "CONNECTED") ?? brokers[0];
        if (connected) setBrokerAccountId(connected.id);
      }),
      refresh(),
    ]).catch((err: Error) => setError(err.message));
  }, []);

  return (
    <section className="card">
      <h1>Orders</h1>
      <p className="muted">PAPER default via Mock broker. LIVE requires TRADING_MODE=LIVE and Dhan connect.</p>
      <DataTable
        columns={["ID", "Symbol", "Side", "Type", "Qty", "Status", "Source"]}
        rows={rows}
        empty="No orders"
      />
      <div className="inline-actions order-form">
        <label>
          Symbol
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        </label>
        <label>
          Qty
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
          />
        </label>
        <button
          type="button"
          disabled={!brokerAccountId}
          onClick={() => {
            setError(null);
            void placeOrder({
              broker_account_id: brokerAccountId,
              symbol,
              exchange: "NSE",
              side: "BUY",
              order_type: "MARKET",
              quantity,
            })
              .then(async () => {
                setMessage("Paper order placed");
                playUiSound("order");
                await refresh();
              })
              .catch((err: Error) => setError(err.message));
          }}
        >
          Place paper order
        </button>
        <button
          type="button"
          className="secondary"
          disabled={rows.length === 0}
          onClick={() => {
            const orderId = rows[0]?.[0];
            if (!orderId) return;
            void cancelOrder(orderId)
              .then(async () => {
                playUiSound("cancel");
                await refresh();
              })
              .catch((err: Error) => setError(err.message));
          }}
        >
          Cancel latest
        </button>
      </div>
      {message ? <p className="muted">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
