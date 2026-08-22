import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

export type HealthResponse = {
  status: string;
  service: string;
};

export type ReadyResponse = {
  status: string;
  service: string;
  checks: {
    database: string;
    redis: string;
  };
  trading_mode: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function getReady(): Promise<ReadyResponse> {
  const { data } = await api.get<ReadyResponse>("/ready");
  return data;
}
