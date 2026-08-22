import { useEffect, useState } from "react";
import { getHealth, getReady, type HealthResponse, type ReadyResponse } from "../services/api";

export function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [ready, setReady] = useState<ReadyResponse | { error: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const h = await getHealth();
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth(null);
      }
      try {
        const r = await getReady();
        if (!cancelled) setReady(r);
      } catch {
        if (!cancelled) setReady({ error: "API not reachable. Start Docker Compose or the backend." });
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="card">
      <h1>Phase 4 dashboard</h1>
      <p>
        GNK Algo is running in <strong>PAPER</strong> mode by default. Live trading is not enabled.
        <a href="/login">Login</a> to open the protected dashboard — mock-labeled capital, order book ticks, and AI
        signal table shell.
      </p>
      <dl className="status-grid">
        <div>
          <dt>API health</dt>
          <dd data-testid="health-status">{health ? `${health.status} · ${health.service}` : "checking…"}</dd>
        </div>
        <div>
          <dt>Readiness</dt>
          <dd data-testid="ready-status">
            {ready && "error" in ready
              ? ready.error
              : ready
                ? `${ready.status} · db ${ready.checks.database} · redis ${ready.checks.redis}`
                : "checking…"}
          </dd>
        </div>
      </dl>
    </section>
  );
}
