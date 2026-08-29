"use client";

import { useState } from "react";

export function CopyButton({
  text,
  label,
  className = "",
}: {
  text: string;
  label: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch {
          /* clipboard may be unavailable */
        }
      }}
      className={`shrink-0 rounded border border-[var(--line)] px-2 py-1 text-[11px] text-slate-300 hover:bg-[var(--panel-2)] ${className}`}
    >
      {copied ? "Copied" : label}
    </button>
  );
}
