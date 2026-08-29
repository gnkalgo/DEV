"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const MOBILE_NAV = [
  { href: "/dashboard", label: "Home" },
  { href: "/orders", label: "Orders" },
  { href: "/positions", label: "Positions" },
  { href: "/signals", label: "AI" },
  { href: "/settings", label: "More" },
];

export function MobileNavigation() {
  const pathname = usePathname();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 flex border-t border-[var(--line)] bg-[var(--panel)]">
      {MOBILE_NAV.map((item) => {
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex-1 py-2.5 text-center text-[10px] font-medium uppercase tracking-wide ${
              active ? "text-[var(--accent)]" : "text-[var(--muted)]"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
