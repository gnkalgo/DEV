"use client";

import { api, getAccessToken } from "@/lib/api";
import { Logo } from "@/components/Logo";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type Plan = { code: string; name: string; days: number; amount_inr: number; label: string };

type PlansResponse = {
  share_url: string;
  upi_vpa: string;
  plans: Plan[];
};

type Checkout = {
  payment_id: string;
  reference: string;
  amount_inr: number;
  days: number;
  plan_code: string;
  intents: { upi: string; gpay: string; phonepe: string; paytm: string; vpa: string; payee: string };
  instructions: string;
};

export default function SubscribePage() {
  const router = useRouter();
  const [data, setData] = useState<PlansResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api<PlansResponse>("/api/v1/billing/plans")
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  async function buy(planCode: string) {
    setError("");
    if (!getAccessToken()) {
      router.push("/login?next=/subscribe");
      return;
    }
    setBusy(planCode);
    try {
      const checkout = await api<Checkout>("/api/v1/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan_code: planCode }),
      }, true);
      sessionStorage.setItem("gnk_checkout", JSON.stringify(checkout));
      router.push(`/subscribe/pay?id=${checkout.payment_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setBusy(null);
    }
  }

  async function copyShare() {
    if (!data?.share_url) return;
    await navigator.clipboard.writeText(data.share_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <Logo href="/" size={48} />
      <p className="mt-8 text-sm uppercase tracking-[0.2em] text-[#2ee6a6]">UPI only · PhonePe · GPay · Paytm</p>
      <h1 className="mt-3 text-4xl font-semibold">Subscribe to GNK ALGO</h1>
      <p className="mt-3 max-w-2xl text-slate-300">
        Share this page with every user. Pay with any UPI app. Access starts after we confirm your UTR.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-3 rounded-2xl border border-[#1d3542] bg-[#0d1b24]/70 p-4">
        <code className="text-sm text-[#2ee6a6]">{data?.share_url || "https://www.gnkalgo.com/subscribe"}</code>
        <button onClick={copyShare} className="rounded-lg bg-[#2ee6a6] px-3 py-1.5 text-sm font-semibold text-[#071018]">
          {copied ? "Copied" : "Copy share link"}
        </button>
      </div>

      {error && <p className="mt-4 text-[#ff6b6b]">{error}</p>}

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {(data?.plans || []).map((plan) => (
          <div key={plan.code} className="rounded-2xl border border-[#1d3542] bg-[#0d1b24]/70 p-5">
            <p className="text-sm text-slate-400">{plan.name}</p>
            <p className="mt-2 text-3xl font-semibold">₹{plan.amount_inr}</p>
            <p className="mt-1 text-sm text-slate-400">{plan.days} day{plan.days > 1 ? "s" : ""}</p>
            <button
              disabled={busy === plan.code}
              onClick={() => buy(plan.code)}
              className="mt-5 w-full rounded-xl bg-[#2ee6a6] py-2.5 text-sm font-semibold text-[#071018]"
            >
              {busy === plan.code ? "Opening UPI…" : "Pay with UPI"}
            </button>
          </div>
        ))}
      </section>
      <p className="mt-8 text-xs text-slate-500">
        Cards, net banking, and wallets other than UPI are not accepted.
        After subscribe, enable <strong className="text-slate-400">auto-renew</strong> in Settings — we email a UPI link before expiry.
      </p>
    </main>
  );
}
