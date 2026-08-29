"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

function VerifyInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function verify() {
    setError("");
    try {
      const res = await api<{ message: string }>("/api/v1/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verify failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <div className="w-full rounded-2xl border border-[#1d3542] bg-[#0d1b24]/80 p-8">
        <h1 className="text-2xl font-semibold">Verify email</h1>
        <p className="mt-2 text-sm text-slate-400 break-all">Token: {token || "missing"}</p>
        <button onClick={verify} className="mt-6 w-full rounded-xl bg-[#2ee6a6] py-2.5 font-semibold text-[#071018]">
          Verify
        </button>
        {error && <p className="mt-3 text-sm text-[#ff6b6b]">{error}</p>}
        {message && <p className="mt-3 text-sm text-[#2ee6a6]">{message}</p>}
        <Link href="/login" className="mt-4 inline-block text-sm text-[#3aa0ff]">Go to login</Link>
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyInner />
    </Suspense>
  );
}
