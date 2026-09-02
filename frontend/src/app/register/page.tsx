"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
import Link from "next/link";
import { Logo } from "@/components/Logo";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [gender, setGender] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    if (fullName.trim().length < 2) {
      setError("Full name must be at least 2 characters.");
      return;
    }
    setLoading(true);
    try {
        const res = await api<{ message: string }>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ full_name: fullName.trim(), email, phone: phone || null, password, gender: gender || null, date_of_birth: dateOfBirth || null }),
      });
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setError("");
    setMessage("");
    try {
      const res = await api<{ message: string }>("/api/v1/auth/resend-verification", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resend failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-6 py-10">
      <form onSubmit={onSubmit} className="w-full rounded-2xl border border-[#1d3542] bg-[#0d1b24]/80 p-8">
        <Logo href="/" size={44} />
        <h1 className="mt-6 text-2xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-slate-400">Password: 12+ chars, upper, lower, digit, special.</p>
        <label className="mt-6 block text-sm">Full name</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={fullName} onChange={(e) => setFullName(e.target.value)} minLength={2} required />
        <label className="mt-4 block text-sm">Email</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label className="mt-4 block text-sm">Phone (India)</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <label className="mt-4 block text-sm">Password</label>
        <div className="relative mt-1"><input className="w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2 pr-14" value={password} onChange={(e) => setPassword(e.target.value)} type={showPassword ? "text" : "password"} required /><button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute inset-y-0 right-0 px-3 text-xs text-slate-400">{showPassword ? "Hide" : "Show"}</button></div>
        <label className="mt-4 block text-sm">Date of birth (DD/MM/YYYY)</label>
        <input className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} type="date" required />
        <label className="mt-4 block text-sm">Gender</label>
        <select className="mt-1 w-full rounded-lg border border-[#1d3542] bg-[#071018] px-3 py-2" value={gender} onChange={(e) => setGender(e.target.value)} required><option value="">Select gender</option><option>Male</option><option>Female</option><option>Other</option></select>
        {error && <p className="mt-3 text-sm text-[#ff6b6b]">{error}</p>}
        {message && <p className="mt-3 text-sm text-[#2ee6a6] break-all">{message}</p>}
        <button disabled={loading} className="mt-6 w-full rounded-xl bg-[#2ee6a6] py-2.5 font-semibold text-[#071018]">
          {loading ? "Creating..." : "Register"}
        </button>
        <button type="button" onClick={resend} className="mt-3 w-full rounded-xl border border-[#1d3542] py-2.5 text-sm">
          Resend verification email
        </button>
        <p className="mt-4 text-sm text-slate-400">
          Already registered? <Link href="/login" className="text-[#2ee6a6]">Login</Link>
        </p>
      </form>
    </main>
  );
}
