"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function HomeBackButton() {
  const pathname = usePathname();
  if (pathname === "/") return null;

  return (
    <Link
      href="/"
      aria-label="Back to home"
      className="fixed bottom-4 right-4 z-[100] rounded-lg border border-[var(--border,#1d3542)] bg-[var(--surface,#0d1b24)]/95 px-3 py-2 text-xs font-medium text-[var(--text-primary,#e2e8f0)] shadow-lg hover:border-[var(--accent,#2ee6a6)] hover:text-[var(--accent,#2ee6a6)]"
    >
      ← Home
    </Link>
  );
}
