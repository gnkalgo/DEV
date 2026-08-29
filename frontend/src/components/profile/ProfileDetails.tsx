"use client";

import { useState } from "react";

import { TerminalInput, TerminalSelect, ErrorBanner } from "@/components/ui/terminal";
import type { Profile } from "@/services/profileService";

export function ProfileDetails({
  profile,
  onSave,
}: {
  profile: Profile;
  onSave: (data: Record<string, unknown>) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState(profile.full_name || "");
  const [displayName, setDisplayName] = useState(profile.display_name || "");
  const [gender, setGender] = useState(profile.gender || "");
  const [dob, setDob] = useState(profile.date_of_birth || "");
  const [phone, setPhone] = useState(profile.phone || "");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function save() {
    setLoading(true);
    setError("");
    try {
      await onSave({
        full_name: fullName,
        display_name: displayName,
        gender: gender || null,
        date_of_birth: dob || null,
        phone: phone || null,
      });
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">
          Profile Details
        </h3>
        {!editing ? (
          <button type="button" onClick={() => setEditing(true)} className="text-xs text-[var(--accent)]">
            Edit
          </button>
        ) : (
          <div className="flex gap-2">
            <button type="button" onClick={() => setEditing(false)} className="text-xs text-[var(--text-secondary)]">
              Cancel
            </button>
            <button type="button" disabled={loading} onClick={save} className="text-xs text-[var(--accent)]">
              {loading ? "Saving…" : "Save Changes"}
            </button>
          </div>
        )}
      </div>
      {error && <ErrorBanner message={error} />}
      <dl className="grid gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Full Name</dt>
          {editing ? (
            <TerminalInput value={fullName} onChange={(e) => setFullName(e.target.value)} className="mt-1 w-full" />
          ) : (
            <dd className="mt-1 text-sm">{profile.full_name || "—"}</dd>
          )}
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Display Name</dt>
          {editing ? (
            <TerminalInput value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="mt-1 w-full" />
          ) : (
            <dd className="mt-1 text-sm">{profile.display_name || "—"}</dd>
          )}
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Gender</dt>
          {editing ? (
            <TerminalSelect value={gender} onChange={(e) => setGender(e.target.value)} className="mt-1 w-full">
              <option value="">—</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </TerminalSelect>
          ) : (
            <dd className="mt-1 text-sm">{profile.gender || "—"}</dd>
          )}
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Date of Birth</dt>
          {editing ? (
            <TerminalInput type="date" value={dob} onChange={(e) => setDob(e.target.value)} className="mt-1 w-full" />
          ) : (
            <dd className="mt-1 text-sm">{profile.date_of_birth || "—"}</dd>
          )}
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Mobile</dt>
          {editing ? (
            <TerminalInput value={phone} onChange={(e) => setPhone(e.target.value)} className="mt-1 w-full" />
          ) : (
            <dd className="mt-1 text-sm">
              {profile.phone || "—"}
              <span className="ml-2 text-[11px] text-[var(--text-secondary)]">
                {profile.phone_verified ? "Verified" : "Not Verified"}
              </span>
            </dd>
          )}
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Email</dt>
          <dd className="mt-1 text-sm">
            {profile.email}
            <span className="ml-2 text-[11px] text-[var(--text-secondary)]">
              {profile.email_verified ? "Verified" : "Not Verified"}
            </span>
          </dd>
        </div>
        <div>
          <dt className="text-[11px] text-[var(--text-secondary)]">Client ID</dt>
          <dd className="mt-1 font-mono text-sm">{profile.client_id}</dd>
        </div>
      </dl>
    </section>
  );
}
