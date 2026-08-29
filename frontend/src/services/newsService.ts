import { api } from "@/lib/api";

export type NewsItem = {
  id: string;
  headline: string;
  summary: string | null;
  source: string;
  published_at: string;
  url: string;
  category: string;
  symbol: string | null;
  thumbnail: string | null;
  is_mock?: boolean;
};

export type NewsResponse = {
  items: NewsItem[];
  updated_at: string;
  source: string;
  symbol: string | null;
};

export async function fetchLatestNews(limit = 10, symbol?: string): Promise<NewsResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (symbol) params.set("symbol", symbol);
  return api<NewsResponse>(`/api/v1/news/latest?${params.toString()}`);
}
