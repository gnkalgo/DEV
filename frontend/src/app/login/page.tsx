"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api, setTokens, TokenBundle } from "@/lib/api";
import Link from "next/link";
import { Logo } from "@/components/Logo";

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfa, setMfa] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const tokens = await api<TokenBundle>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, mfa_code: mfa || null }),
      });
      setTokens(tokens);
      router.push(search.get("next") || "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <form onSubmit={onSubmit} className="w-full rounded-2xl border border-[#1d3542] bg-[#0d1b24]/80 p-8">
        <Logo href="/" size={44} />
        <h1 className="mt-6 text-2xl font-semibold">Login</h1>
        <p className="mt-1 text-sm text-slate-400">GnKAlgo account</p>
        <label className="mt-6 block text-sm">Email</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label className="mt-4 block text-sm">Password</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        <label className="mt-4 block text-sm">MFA code (if enabled)</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={mfa} onChange={(e) => setMfa(e.target.value)} inputMode="numeric" />
        {error && <p className="mt-3 text-sm text-[#ff6b6b]">{error}</p>}
        <button disabled={loading} className="mt-6 w-full rounded-xl bg-[#2ee6a6] py-2.5 font-semibold text-[#071018]">
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="mt-4 text-sm text-slate-400">
          No account? <Link href="/register" className="text-[#2ee6a6]">Register</Link>
          {" · "}
          <Link href="/forgot-password" className="text-[#3aa0ff]">Forgot password</Link>
        </p>
      </form>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="p-10 text-slate-400">Loading…</main>}>
      <LoginForm />
    </Suspense>
  );
}
