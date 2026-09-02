"use client";

import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { Logo } from "@/components/Logo";

function LoginForm() {
  const router = useRouter();
  const search = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mfa, setMfa] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, mfa_code: mfa || null }),
      });
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
        {search.get("verified") === "1" && <p className="mt-3 rounded-lg border border-[#2ee6a6]/40 bg-[#2ee6a6]/10 p-3 text-sm text-[#2ee6a6]">Email verified successfully. You can now sign in.</p>}
        <label className="mt-6 block text-sm">Email</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label className="mt-4 block text-sm">Password</label>
        <div className="relative mt-1">
          <input className="w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2 pr-14" value={password} onChange={(e) => setPassword(e.target.value)} type={showPassword ? "text" : "password"} required />
          <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"} className="absolute inset-y-0 right-0 px-3 text-xs text-slate-400">{showPassword ? "Hide" : "Show"}</button>
        </div>
        <label className="mt-4 block text-sm">MFA code (if enabled)</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={mfa} onChange={(e) => setMfa(e.target.value)} placeholder="6-digit TOTP or backup code" />
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
