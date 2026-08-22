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

export type UserPublic = {
  id: string;
  email: string;
  mobile: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
};

export type AuthResponse = {
  success: boolean;
  user: UserPublic;
};

function apiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: { message?: string } } | undefined;
    return data?.error?.message ?? fallback;
  }
  return fallback;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function getReady(): Promise<ReadyResponse> {
  const { data } = await api.get<ReadyResponse>("/ready");
  return data;
}

export async function registerUser(body: {
  full_name: string;
  email: string;
  mobile: string;
  password: string;
  confirm_password: string;
}): Promise<AuthResponse> {
  try {
    const { data } = await api.post<AuthResponse>("/auth/register", body);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Registration failed"));
  }
}

export async function loginUser(body: { email: string; password: string }): Promise<AuthResponse> {
  try {
    const { data } = await api.post<AuthResponse>("/auth/login", body);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Login failed"));
  }
}

export async function logoutUser(): Promise<void> {
  await api.post("/auth/logout");
}

export async function getMe(): Promise<AuthResponse> {
  const { data } = await api.get<AuthResponse>("/auth/me");
  return data;
}

export async function getDashboard(): Promise<import("../types/dashboard").DashboardResponse> {
  const { data } = await api.get<import("../types/dashboard").DashboardResponse>("/dashboard");
  return data;
}
