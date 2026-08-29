"use client";

import { useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, Skeleton } from "@/components/ui/terminal";
import { fetchLatestNews, type NewsItem } from "@/services/newsService";

const CATEGORIES = ["all", "market", "stocks", "economy", "ipo", "company", "global"];

function NewsCard({ item }: { item: NewsItem }) {
  const time = new Date(item.published_at).toLocaleString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block border-b border-[var(--border)] py-3 last:border-b-0 hover:bg-[var(--surface-secondary)]/50 px-2 -mx-2 rounded"
    >
      <p className="text-sm font-medium text-[var(--text-primary)] leading-snug">{item.headline}</p>
      <p className="mt-1 text-[11px] text-[var(--text-secondary)]">
        {item.source} · {time}
        {item.is_mock && <span className="ml-2 text-[var(--warning)]">MOCK</span>}
      </p>
      {item.summary && (
        <p className="mt-1 text-xs text-[var(--text-secondary)] line-clamp-2">{item.summary}</p>
      )}
    </a>
  );
}

export function LatestNews({ symbol }: { symbol?: string }) {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [category, setCategory] = useState("all");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchLatestNews(10, symbol);
      setItems(res.items);
      setUpdatedAt(res.updated_at);
      setSource(res.source);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load market news.");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    load();
    const timer = setInterval(load, 3 * 60 * 1000);
    return () => clearInterval(timer);
  }, [load]);

  const filtered =
    category === "all"
      ? items
      : items.filter((i) => i.category.toLowerCase() === category);

  return (
    <section className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">
          Latest News
          {symbol && <span className="ml-2 text-[var(--accent)]">{symbol}</span>}
        </h3>
        <div className="flex items-center gap-2 text-[10px] text-[var(--text-secondary)]">
          {updatedAt && (
            <span>
              Updated {new Date(updatedAt).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
          <button type="button" onClick={load} className="text-[var(--accent)]">Refresh</button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setCategory(c)}
            className={`rounded px-2 py-0.5 text-[10px] uppercase ${
              category === c
                ? "bg-[var(--accent)] text-black"
                : "border border-[var(--border)] text-[var(--text-secondary)]"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {error && <ErrorBanner message={error} />}
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : filtered.length ? (
        <div>
          {filtered.slice(0, 8).map((item) => (
            <NewsCard key={item.id} item={item} />
          ))}
          {source === "mock_dev" && (
            <p className="mt-2 text-[10px] text-[var(--warning)]">Development mock news — not live market data.</p>
          )}
        </div>
      ) : (
        <EmptyState title="No recent news available." />
      )}
    </section>
  );
}
