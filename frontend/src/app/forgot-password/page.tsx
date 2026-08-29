"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import { Logo } from "@/components/Logo";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const res = await api<{ message: string }>("/api/v1/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <form onSubmit={onSubmit} className="w-full rounded-2xl border border-[#1d3542] bg-[#0d1b24]/80 p-8">
        <Logo href="/" size={44} />
        <h1 className="mt-6 text-2xl font-semibold">Reset password</h1>
        <input className="mt-6 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        {error && <p className="mt-3 text-sm text-[#ff6b6b]">{error}</p>}
        {message && <p className="mt-3 text-sm text-[#2ee6a6] break-all">{message}</p>}
        <button className="mt-6 w-full rounded-xl bg-[#2ee6a6] py-2.5 font-semibold text-[#071018]">Send reset link</button>
      </form>
    </main>
  );
}
