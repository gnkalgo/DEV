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

export type BrokerPublic = {
  id: string;
  broker: string;
  client_id: string;
  status: string;
  has_api_key: boolean;
  has_api_secret: boolean;
  has_totp: boolean;
  created_at: string;
  updated_at: string;
};

export type BrokerActionResponse = {
  success: boolean;
  broker: BrokerPublic;
  message?: string;
  metadata?: Record<string, string>;
};

export type OrderPublic = {
  id: string;
  broker_account_id: string;
  symbol: string;
  exchange: string;
  segment: string;
  side: string;
  order_type: string;
  quantity: number;
  price: string | null;
  status: string;
  broker_order_id: string | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export async function listBrokers(): Promise<BrokerPublic[]> {
  const { data } = await api.get<{ brokers: BrokerPublic[] }>("/brokers");
  return data.brokers;
}

export async function saveBroker(body: {
  broker: string;
  client_id: string;
  api_key?: string;
  api_secret?: string;
  totp?: string;
}): Promise<BrokerPublic> {
  try {
    const { data } = await api.post<BrokerActionResponse>("/brokers", body);
    return data.broker;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Failed to save broker"));
  }
}

export async function connectBroker(
  brokerAccountId: string,
  body?: { access_token?: string },
): Promise<BrokerActionResponse> {
  try {
    const { data } = await api.post<BrokerActionResponse>(`/brokers/${brokerAccountId}/connect`, body ?? {});
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Connect failed"));
  }
}

export async function disconnectBroker(brokerAccountId: string): Promise<BrokerActionResponse> {
  try {
    const { data } = await api.post<BrokerActionResponse>(`/brokers/${brokerAccountId}/disconnect`);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Disconnect failed"));
  }
}

export async function testBroker(brokerAccountId: string): Promise<BrokerActionResponse> {
  try {
    const { data } = await api.post<BrokerActionResponse>(`/brokers/${brokerAccountId}/test`);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Test connection failed"));
  }
}

export async function listOrders(): Promise<OrderPublic[]> {
  const { data } = await api.get<{ orders: OrderPublic[] }>("/orders");
  return data.orders;
}

export async function placeOrder(body: {
  broker_account_id: string;
  symbol: string;
  exchange?: string;
  segment?: string;
  side: "BUY" | "SELL";
  order_type: "MARKET" | "LIMIT" | "SL" | "SL-M";
  quantity: number;
  price?: number;
  security_id?: string;
  idempotency_key?: string;
}): Promise<OrderPublic> {
  try {
    const { data } = await api.post<OrderPublic>("/orders", body);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Order placement failed"));
  }
}

export async function cancelOrder(orderId: string): Promise<OrderPublic> {
  try {
    const { data } = await api.post<OrderPublic>(`/orders/${orderId}/cancel`);
    return data;
  } catch (error) {
    throw new Error(apiErrorMessage(error, "Cancel failed"));
  }
}
