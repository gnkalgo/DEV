import { Logo } from "@/components/Logo";

const FEATURES = [
  { title: "Predict", body: "AI-powered market insights." },
  { title: "Analyze", body: "Advanced charting and technical analysis." },
  { title: "Execute", body: "One-click trade execution." },
  { title: "Manage risk", body: "Smart risk management." },
  { title: "Automate", body: "Algo strategies and automation." },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <Logo size={72} />
      <p className="mt-8 text-sm uppercase tracking-[0.2em] text-[#2ee6a6]">Indian markets · NSE / BSE / MCX</p>
      <h1 className="mt-4 text-5xl font-semibold leading-tight">
        GNK <span className="bg-gradient-to-b from-[#2ee6a6] to-[#3aa0ff] bg-clip-text text-transparent">ALGO</span>
      </h1>
      <p className="mt-3 text-sm uppercase tracking-[0.22em] text-slate-400">Intelligence behind every trade</p>
      <p className="mt-4 max-w-2xl text-lg text-slate-300">
        Algo trading platform for the Indian stock market. Connect Dhan and Groww, run strategies,
        consume TradingView webhooks, and generate AI signals.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <a href="/subscribe" className="rounded-xl bg-[#2ee6a6] px-5 py-3 text-sm font-semibold text-[#071018]">
          Subscribe (UPI)
        </a>
        <a href="/register" className="rounded-xl border border-[#1d3542] px-5 py-3 text-sm">
          Create account
        </a>
        <a href="/login" className="rounded-xl border border-[#1d3542] px-5 py-3 text-sm">
          Login
        </a>
      </div>
      <section className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {FEATURES.map((item) => (
          <div key={item.title} className="rounded-2xl border border-[#1d3542] bg-[#0d1b24]/70 p-4">
            <h2 className="font-medium text-[#2ee6a6]">{item.title}</h2>
            <p className="mt-2 text-sm text-slate-400">{item.body}</p>
          </div>
        ))}
      </section>
      <p className="mt-10 text-xs text-slate-500">
        Not investment advice. Trading involves risk. Use paper mode until you understand the flow.
      </p>
    </main>
  );
}
