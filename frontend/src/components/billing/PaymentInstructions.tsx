"use client";

import { CopyButton } from "@/components/billing/CopyButton";

type PaymentInstructionsProps = {
  amount_inr: number;
  vpa: string;
  payee: string;
  reference: string;
  className?: string;
};

/**
 * Displays UPI payment instructions without truncating the VPA or reference.
 * VPA and reference use whitespace-nowrap + shrink-0 so flex parents cannot clip digits.
 */
export function PaymentInstructions({
  amount_inr,
  vpa,
  payee,
  reference,
  className = "",
}: PaymentInstructionsProps) {
  return (
    <section
      className={`rounded-2xl border border-[#1d3542] bg-[#0d1b24]/70 p-5 overflow-visible ${className}`}
    >
      <h2 className="text-sm font-medium text-[#2ee6a6]">Payment instructions</h2>

      <div className="mt-3 break-words text-sm text-slate-300 leading-relaxed">
        Send exactly ₹{amount_inr} to{" "}
        <span className="inline-flex flex-wrap items-center gap-2 align-middle">
          <span className="font-mono font-semibold whitespace-nowrap shrink-0 overflow-visible text-[#2ee6a6]">
            {vpa}
          </span>
          <CopyButton text={vpa} label="Copy UPI ID" />
        </span>
        {" "}
        ({payee}).
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-slate-300">
        <span>Reference:</span>
        <span className="font-mono font-semibold whitespace-nowrap shrink-0 overflow-visible text-white">
          {reference}
        </span>
        <CopyButton text={reference} label="Copy reference" />
      </div>
    </section>
  );
}
