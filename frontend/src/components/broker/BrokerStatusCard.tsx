"use client";

import Link from "next/link";

import { fmtTime } from "@/lib/format";

type BrokerStatus = {
  broker: string;
  status: string;
  client_id?: string | null;
  health_status?: string;
  last_health_check?: string | null;
  error?: string | null;
};

export function BrokerStatusCard({
  status,
  onRefresh,
  loading,
}: {
  status: BrokerStatus | null;
  onRefresh?: () => void;
  loading?: boolean;
}) {
  const connected = status?.status === "connected";
  const statusColor = connected
    ? "text-[var(--profit)]"
    : status?.status === "error"
      ? "text-[var(--loss)]"
      : "text-[var(--muted)]";

  return (
    <div className="rounded border border-[var(--line)] bg-[var(--panel)] p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-white">Dhan</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">GnKAlgo broker integration</p>
        </div>
        <span className={`text-xs font-semibold uppercase ${statusColor}`}>
          {status?.status ?? "disconnected"}
        </span>
      </div>
      <dl className="mt-4 space-y-2 text-xs">
        <div className="flex justify-between">
          <dt className="text-[var(--muted)]">Client ID</dt>
          <dd className="text-white">{status?.client_id ?? "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-[var(--muted)]">Health</dt>
          <dd className="text-white">{status?.health_status ?? "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-[var(--muted)]">Last Sync</dt>
          <dd className="text-white">{fmtTime(status?.last_health_check)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-[var(--muted)]">Trading API</dt>
          <dd className={connected ? "text-[var(--profit)]" : "text-[var(--muted)]"}>
            {connected ? "Connected" : "Disconnected"}
          </dd>
        </div>
      </dl>
      {status?.error && (
        <p className="mt-3 text-xs text-[var(--loss)]">{status.error}</p>
      )}
      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/settings#broker"
          className="rounded bg-[var(--accent)] px-3 py-1.5 text-xs font-semibold text-black"
        >
          {connected ? "Reconnect" : "Connect"}
        </Link>
        {onRefresh && (
          <button
            type="button"
            disabled={loading}
            onClick={onRefresh}
            className="rounded border border-[var(--line)] px-3 py-1.5 text-xs disabled:opacity-50"
          >
            {loading ? "Refreshing…" : "Refresh Account"}
          </button>
        )}
      </div>
      <p className="mt-3 text-[10px] text-[var(--muted)]">
        Access tokens are never shown here. Configure credentials in Profile settings.
      </p>
    </div>
  );
}
