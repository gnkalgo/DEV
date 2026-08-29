"use client";

import type { Profile } from "@/services/profileService";

function statusLabel(status: string) {
  if (status === "ACTIVE") return { text: "ACTIVE", className: "text-[var(--positive)]" };
  if (status === "PENDING") return { text: "PENDING", className: "text-[var(--warning)]" };
  if (status === "NOT_AVAILABLE") return { text: "NOT AVAILABLE", className: "text-[var(--text-secondary)]" };
  return { text: "INACTIVE", className: "text-[var(--text-secondary)]" };
}

export function TradingSegments({ segments }: { segments: Profile["trading_segments"] }) {
  return (
    <section className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)] mb-3">
        Trading Segments
      </h3>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {segments.map((s) => {
          const st = statusLabel(s.status);
          return (
            <div
              key={s.code}
              className="rounded border border-[var(--border)] bg-[var(--surface-secondary)] px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--accent)]">{s.icon}</span>
                <span className="text-sm font-medium text-[var(--text-primary)]">{s.name}</span>
              </div>
              <p className={`mt-1 text-[10px] font-semibold uppercase ${st.className}`}>
                {st.text}
              </p>
              {s.status === "INACTIVE" && s.code !== "currency" && s.code !== "commodities" && (
                <p className="mt-1 text-[10px] text-[var(--text-secondary)]">
                  Connect broker to activate
                </p>
              )}
              {(s.status === "NOT_AVAILABLE" || s.code === "currency" || s.code === "commodities") && s.status !== "ACTIVE" && (
                <p className="mt-1 text-[10px] text-[var(--text-secondary)]">
                  KYC / broker activation required
                </p>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
