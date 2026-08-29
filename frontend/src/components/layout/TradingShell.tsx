"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { MobileNavigation } from "@/components/layout/MobileNavigation";
import { TradingHeader } from "@/components/layout/TradingHeader";
import { TradingSidebar } from "@/components/layout/TradingSidebar";
import { api, getAccessToken } from "@/lib/api";

export function TradingShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login?next=" + encodeURIComponent(pathname));
      return;
    }
    api<{ is_admin?: boolean }>("/api/v1/auth/me", {}, true)
      .then((me) => setIsAdmin(Boolean(me.is_admin)))
      .catch(() => setIsAdmin(false));
  }, [router, pathname]);

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <TradingHeader />
      <div className="flex flex-1 min-h-0">
        <TradingSidebar isAdmin={isAdmin} />
        <main className="flex-1 min-w-0 p-3 md:p-4 pb-16 lg:pb-4 overflow-x-hidden">
          {children}
        </main>
      </div>
      <MobileNavigation />
    </div>
  );
}

/** @deprecated Use TradingShell — kept for gradual migration */
export function AppShell({ children }: { children: React.ReactNode }) {
  return <TradingShell>{children}</TradingShell>;
}
