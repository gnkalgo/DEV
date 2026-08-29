"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { clearTokens } from "@/lib/api";
import { fetchProfile, type Profile } from "@/services/profileService";
import { useRouter } from "next/navigation";

function initials(profile: Profile | null) {
  if (!profile) return "?";
  const name = profile.display_name || profile.full_name || profile.email;
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

export function UserMenu() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [profile, setProfile] = useState<Profile | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchProfile().then(setProfile).catch(() => setProfile(null));
  }, []);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded border border-[var(--border)] px-2 py-1 hover:bg-[var(--surface-secondary)]"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--surface-secondary)] text-[10px] font-bold text-[var(--accent)] overflow-hidden">
          {profile?.profile_photo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={profile.profile_photo_url} alt="" className="h-full w-full object-cover" />
          ) : (
            initials(profile)
          )}
        </span>
        <span className="hidden md:block text-left max-w-[120px]">
          <span className="block text-[11px] font-medium text-[var(--text-primary)] truncate">
            {profile?.display_name || profile?.full_name || "Account"}
          </span>
          {profile?.client_id && (
            <span className="block text-[9px] text-[var(--text-secondary)] truncate">{profile.client_id}</span>
          )}
        </span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 w-48 rounded border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg"
        >
          <div className="px-3 py-2 border-b border-[var(--border)]">
            <p className="text-xs font-medium truncate">{profile?.display_name || profile?.email}</p>
            <p className="text-[10px] text-[var(--text-secondary)]">{profile?.client_id}</p>
          </div>
          {[
            { href: "/profile", label: "Profile" },
            { href: "/settings/security/devices", label: "Connected Devices" },
            { href: "/settings", label: "Settings" },
            { href: "/subscribe", label: "Subscription" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block px-3 py-2 text-xs hover:bg-[var(--surface-secondary)]"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
          <button
            type="button"
            className="w-full px-3 py-2 text-left text-xs text-[var(--negative)] hover:bg-[var(--surface-secondary)]"
            onClick={() => {
              clearTokens();
              router.replace("/login");
            }}
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}
