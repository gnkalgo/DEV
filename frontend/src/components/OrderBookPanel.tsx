import { useState } from "react";
import type { DashboardResponse } from "../types/dashboard";
import { playUiSound } from "../utils/sounds";

type Level = { price: string; quantity: number };

export function OrderBookPanel({ book }: { book: DashboardResponse["order_book"] }) {
  const [bids, setBids] = useState<Level[]>(book.bids);
  const [asks, setAsks] = useState<Level[]>(book.asks);

  function simulateUpdate() {
    const next = (Number(bids[0]?.price || "0") + 0.05).toFixed(2);
    setBids([{ price: next, quantity: 50 }, ...bids.slice(0, 3)]);
    setAsks([{ price: (Number(next) + 0.05).toFixed(2), quantity: 40 }, ...asks.slice(0, 3)]);
    playUiSound("order");
  }

  function simulateCancel() {
    setBids((current) => current.slice(1));
    playUiSound("cancel");
  }

  return (
    <article className="card widget" data-testid="order-book">
      <h2>Order book</h2>
      <p className="muted">
        {book.symbol} · source {book.source} · sounds play only on these actions, not on login
      </p>
      <div className="book-grid">
        <div>
          <h3>Bids</h3>
          <ul>
            {bids.map((level, idx) => (
              <li key={`b-${idx}`}>
                {level.price} × {level.quantity}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Asks</h3>
          <ul>
            {asks.map((level, idx) => (
              <li key={`a-${idx}`}>
                {level.price} × {level.quantity}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="inline-actions">
        <button type="button" onClick={simulateUpdate}>
          Simulate book update
        </button>
        <button type="button" className="secondary" onClick={simulateCancel}>
          Simulate cancel
        </button>
      </div>
    </article>
  );
}
