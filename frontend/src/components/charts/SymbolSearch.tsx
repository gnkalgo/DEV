"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { TerminalInput } from "@/components/ui/terminal";
import { searchInstruments, type Instrument } from "@/services/chartDataService";

function segmentLabel(segment: string) {
  if (segment === "FNO") return "F&O";
  if (segment === "INDEX") return "IDX";
  return segment;
}

export function SymbolSearch({
  symbol,
  exchange,
  onSelect,
  segmentFilter,
  placeholder = "Symbol",
}: {
  symbol: string;
  exchange: string;
  onSelect: (inst: Instrument) => void;
  segmentFilter?: string;
  placeholder?: string;
}) {
  const [query, setQuery] = useState(symbol);
  const [results, setResults] = useState<Instrument[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) {
        setResults([]);
        return;
      }
      try {
        const items = await searchInstruments(q, {
          limit: 20,
          segment: segmentFilter,
        });
        setResults(items);
      } catch {
        setResults([]);
      }
    },
    [segmentFilter],
  );

  useEffect(() => {
    setQuery(symbol);
  }, [symbol]);

  const handleChange = (value: string) => {
    const v = value.toUpperCase();
    setQuery(v);
    setOpen(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => runSearch(v), 200);
  };

  return (
    <div className="relative min-w-[140px]">
      <label className="text-[10px] uppercase text-[var(--muted)]">Search</label>
      <TerminalInput
        value={query}
        onChange={(e) => handleChange(e.target.value)}
        onFocus={() => {
          setOpen(true);
          runSearch(query);
        }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder={placeholder}
        className="mt-0.5 w-full min-w-[120px]"
      />
      {open && results.length > 0 && (
        <ul
          className="absolute z-30 mt-1 max-h-48 w-full min-w-[260px] overflow-auto rounded border border-[var(--line)] bg-[var(--panel)] shadow-lg"
        >
          {results.map((item) => (
            <li key={`${item.symbol}-${item.exchange}-${item.security_id}`}>
              <button
                type="button"
                className="flex w-full flex-col px-2.5 py-1.5 text-left hover:bg-[var(--panel-2)]"
                onMouseDown={() => {
                  onSelect(item);
                  setQuery(item.symbol);
                  setOpen(false);
                }}
              >
                <span className="text-xs font-medium text-white">
                  {item.symbol}
                  <span className="ml-2 rounded bg-[var(--panel-2)] px-1 text-[9px] text-[var(--muted)]">
                    {segmentLabel(item.segment)}
                  </span>
                  <span className="ml-1 text-[10px] text-[var(--muted)]">{item.exchange}</span>
                </span>
                <span className="text-[10px] text-[var(--muted)] line-clamp-1">{item.display_name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && query && results.length === 0 && (
        <p className="absolute z-30 mt-1 w-full rounded border border-[var(--line)] bg-[var(--panel)] px-2 py-1.5 text-[10px] text-[var(--muted)]">
          No instruments found
        </p>
      )}
      <span className="mt-0.5 block text-[10px] text-[var(--muted)]">{exchange}</span>
    </div>
  );
}
