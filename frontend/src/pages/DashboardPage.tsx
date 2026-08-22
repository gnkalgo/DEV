import { useEffect, useState } from "react";
import { BrokerForm } from "../components/BrokerForm";
import { DataTable } from "../components/DataTable";
import { IpModal } from "../components/IpModal";
import { OrderBookPanel } from "../components/OrderBookPanel";
import { StatusCard } from "../components/StatusCard";
import { getDashboard } from "../services/api";
import type { DashboardResponse } from "../types/dashboard";

export function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ipOpen, setIpOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getDashboard()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => {
        if (!cancelled) setError("Could not load dashboard.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <section className="card">
        <p className="form-error">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="card">
        <p>Loading dashboard…</p>
      </section>
    );
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      <p className="muted">
        Mode <strong>{data.trading_mode}</strong> · env {data.environment}. Capital figures are mock-labeled until a
        broker is connected.
      </p>
      <div className="widget-grid">
        <StatusCard title="Market status">
          <p>
            {data.market.segment}: <strong>{data.market.status}</strong>
          </p>
          <p className="muted">{data.market.note}</p>
        </StatusCard>
        <StatusCard title="Broker status">
          <p>
            <strong>{data.broker.status}</strong>
          </p>
          <p className="muted">{data.broker.note}</p>
        </StatusCard>
        <StatusCard title="Capital / margin">
          <p className="badge">MOCK</p>
          <dl className="status-grid">
            <div>
              <dt>Available</dt>
              <dd>
                {data.capital.currency} {data.capital.available}
              </dd>
            </div>
            <div>
              <dt>Margin used</dt>
              <dd>{data.capital.margin_used}</dd>
            </div>
            <div>
              <dt>Day P&L</dt>
              <dd>{data.capital.day_pnl}</dd>
            </div>
            <div>
              <dt>Exposure</dt>
              <dd>{data.capital.exposure}</dd>
            </div>
          </dl>
        </StatusCard>
      </div>
      <StatusCard title="Broker configuration">
        <BrokerForm />
      </StatusCard>
      <StatusCard title="AI signals">
        <p className="muted">Table structure only. No ML engine in Phases 0–6.</p>
        <DataTable
          columns={["Ticker", "Segment", "AI Trend", "Confidence", "Strategy State", "Entry", "SL", "Target", "Status"]}
          rows={data.signals.map((row) => [
            row.ticker,
            row.segment,
            row.ai_trend,
            row.confidence,
            row.strategy_state,
            row.entry,
            row.sl,
            row.target,
            row.status,
          ])}
          empty="No signal rows"
        />
      </StatusCard>
      <StatusCard title="Positions">
        <DataTable
          columns={["Symbol", "Exchange", "Qty", "Avg", "Unrealized P&L"]}
          rows={data.positions.map((row) => [
            row.symbol,
            row.exchange,
            String(row.quantity),
            row.average_price,
            row.unrealized_pnl,
          ])}
          empty="No positions until a broker is connected"
        />
      </StatusCard>
      <StatusCard title="Orders">
        <DataTable
          columns={["ID", "Symbol", "Side", "Type", "Qty", "Status", "Source"]}
          rows={data.orders.map((row) => [
            row.id,
            row.symbol,
            row.side,
            row.order_type,
            String(row.quantity),
            row.status,
            row.source,
          ])}
          empty="No orders yet. Paper actions arrive with the Mock broker (Phase 5)."
        />
      </StatusCard>
      <OrderBookPanel book={data.order_book} />
      <p>
        <button type="button" className="secondary" onClick={() => setIpOpen(true)}>
          IP details
        </button>
      </p>
      <IpModal details={data.ip_details} open={ipOpen} onClose={() => setIpOpen(false)} />
    </div>
  );
}
