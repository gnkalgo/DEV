"use client";

import { FormEvent, Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import Link from "next/link";

function ResetInner() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      const res = await api<{ message: string }>("/api/v1/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6">
      <form onSubmit={onSubmit} className="w-full rounded-2xl border border-[#1d3542] bg-[#0d1b24]/80 p-8">
        <h1 className="text-2xl font-semibold">Set new password</h1>
        <input className="mt-6 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="mt-3 text-sm text-[#ff6b6b]">{error}</p>}
        {message && <p className="mt-3 text-sm text-[#2ee6a6]">{message}</p>}
        <button className="mt-6 w-full rounded-xl bg-[#2ee6a6] py-2.5 font-semibold text-[#071018]">Update password</button>
        <Link href="/login" className="mt-4 inline-block text-sm text-[#3aa0ff]">Back to login</Link>
      </form>
    </main>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetInner />
    </Suspense>
  );
}
