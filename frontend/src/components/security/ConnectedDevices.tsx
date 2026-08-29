"use client";

import { useEffect, useState } from "react";

import { ErrorBanner, Skeleton } from "@/components/ui/terminal";
import {
  fetchSessions,
  logoutOtherDevices,
  logoutSession,
  type DeviceSession,
} from "@/services/sessionService";
import { fmtTime } from "@/lib/format";

function DeviceCard({
  session,
  onLogout,
}: {
  session: DeviceSession;
  onLogout: (id: string) => void;
}) {
  return (
    <div className="rounded border border-[var(--border)] bg-[var(--surface-secondary)] p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-[var(--text-primary)]">
            {session.browser} on {session.os}
          </p>
          <p className="text-[11px] text-[var(--text-secondary)]">{session.device_type}</p>
          <p className="text-[11px] text-[var(--text-secondary)]">{session.location}</p>
          <p className="text-[11px] text-[var(--text-secondary)]">
            IP: {session.ip_address || "—"}
          </p>
          <p className="text-[11px] text-[var(--text-secondary)]">
            Last active: {fmtTime(session.last_active_at || session.login_time)}
          </p>
          {session.is_current && (
            <span className="mt-1 inline-block text-[10px] font-bold uppercase text-[var(--accent)]">
              THIS DEVICE
            </span>
          )}
        </div>
        {session.status === "active" && !session.is_current && (
          <button
            type="button"
            onClick={() => onLogout(session.id)}
            className="rounded border border-[var(--border)] px-2 py-1 text-[11px] text-[var(--negative)]"
          >
            Log out device
          </button>
        )}
        {session.status !== "active" && (
          <span className="text-[10px] uppercase text-[var(--text-secondary)]">{session.status}</span>
        )}
      </div>
    </div>
  );
}

export function ConnectedDevices() {
  const [sessions, setSessions] = useState<DeviceSession[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [confirmLogoutOthers, setConfirmLogoutOthers] = useState(false);
  const [logoutLoading, setLogoutLoading] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setSessions(await fetchSessions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load devices");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleLogoutOthers() {
    setLogoutLoading(true);
    try {
      await logoutOtherDevices();
      setConfirmLogoutOthers(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Logout failed");
    } finally {
      setLogoutLoading(false);
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="text-xs font-semibold uppercase text-[var(--text-secondary)]">
          Connected Devices
        </h3>
        <button
          type="button"
          onClick={() => setConfirmLogoutOthers(true)}
          className="text-xs text-[var(--negative)]"
        >
          Log out all other devices
        </button>
      </div>
      {error && <ErrorBanner message={error} />}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <DeviceCard
              key={s.id}
              session={s}
              onLogout={async (id) => {
                await logoutSession(id);
                await load();
              }}
            />
          ))}
          {!sessions.length && (
            <p className="text-sm text-[var(--text-secondary)]">No active sessions found.</p>
          )}
        </div>
      )}

      {confirmLogoutOthers && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-sm rounded border border-[var(--border)] bg-[var(--surface)] p-4">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">Log out all other devices?</h4>
            <p className="mt-2 text-xs text-[var(--text-secondary)]">
              You&apos;ll remain signed in on this device. Other active GnKAlgo sessions will be terminated.
            </p>
            <div className="mt-4 flex gap-2">
              <button
                type="button"
                onClick={() => setConfirmLogoutOthers(false)}
                className="flex-1 rounded border border-[var(--border)] py-2 text-xs"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={logoutLoading}
                onClick={handleLogoutOthers}
                className="flex-1 rounded bg-[var(--negative)] py-2 text-xs font-semibold text-white disabled:opacity-50"
              >
                {logoutLoading ? "Logging out…" : "Log Out Devices"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
