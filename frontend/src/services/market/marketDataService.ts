import { api } from "@/lib/api";
import type { MarketIndicesResponse, MarketIndex, MarketStatus } from "./marketTypes";

type Listener = () => void;

class MarketDataService {
  private indices: MarketIndex[] = [];
  private status: MarketStatus | null = null;
  private source = "";
  private listeners = new Set<Listener>();
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private connecting = false;

  getIndices(): MarketIndex[] {
    return this.indices;
  }

  getStatus(): MarketStatus | null {
    return this.status;
  }

  getSource(): string {
    return this.source;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((l) => l());
  }

  async fetchSnapshot(): Promise<void> {
    if (this.connecting) return;
    this.connecting = true;
    try {
      const [indicesRes, statusRes] = await Promise.all([
        api<MarketIndicesResponse>("/api/v1/market/indices"),
        api<MarketStatus>("/api/v1/market/status"),
      ]);
      this.indices = indicesRes.indices;
      this.status = statusRes;
      this.source = indicesRes.source;
      this.notify();
    } finally {
      this.connecting = false;
    }
  }

  connect(pollMs = 15000): void {
    this.fetchSnapshot();
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(() => this.fetchSnapshot(), pollMs);
  }

  disconnect(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }
}

export const marketDataService = new MarketDataService();
