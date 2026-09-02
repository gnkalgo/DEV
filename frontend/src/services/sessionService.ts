import { api } from "@/lib/api";

export type DeviceSession = {
  id: string;
  device_type: string;
  browser: string;
  os: string;
  location: string;
  ip_address: string | null;
  last_active_at: string | null;
  login_time: string;
  is_current: boolean;
  status: "active" | "revoked" | "expired";
};

export async function fetchSessions(): Promise<DeviceSession[]> {
  return api<DeviceSession[]>("/api/v1/auth/sessions", {}, true);
}

export async function logoutSession(sessionId: string): Promise<void> {
  await api(`/api/v1/auth/sessions/${sessionId}`, { method: "DELETE" }, true);
}

export async function logoutOtherDevices(): Promise<string> {
  const res = await api<{ message: string }>("/api/v1/auth/sessions/logout-others", {
    method: "POST",
    body: JSON.stringify({}),
  }, true);
  return res.message;
}
