"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/profile", label: "Profile" },
  { href: "/settings/appearance", label: "Appearance" },
  { href: "/settings/security/devices", label: "Connected Devices" },
  { href: "/settings", label: "Account & Broker" },
  { href: "/subscribe", label: "Subscription" },
];

export function SettingsNav() {
  const pathname = usePathname();
  return (
    <nav className="mb-4 flex flex-wrap gap-1 border-b border-[var(--border)] pb-2">
      {LINKS.map((item) => {
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded px-2.5 py-1.5 text-[11px] font-medium ${
              active ? "bg-[var(--surface-secondary)] text-[var(--accent)]" : "text-[var(--text-secondary)]"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
