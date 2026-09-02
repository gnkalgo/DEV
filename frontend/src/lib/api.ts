function resolveApiBase(): string {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    }
    return "";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function clearTokens() { /* The server clears authentication cookies. */ }

function cookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const item = document.cookie.split("; ").find((part) => part.startsWith(`${name}=`));
  return item ? decodeURIComponent(item.slice(name.length + 1)) : null;
}

type ValidationIssue = { loc?: Array<string | number>; msg?: string };

function errorDetail(data: unknown, fallback: string): string {
  const detail = (data as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((issue: ValidationIssue) => {
      const field = issue.loc?.filter((part) => part !== "body").at(-1);
      const label = typeof field === "string"
        ? field.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase())
        : "Input";
      return `${label}: ${issue.msg || "Invalid value"}`;
    }).join(". ");
  }
  return fallback;
}

async function refreshAccessToken(): Promise<boolean> {
  const res = await fetch(`${resolveApiBase()}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": cookie("gnk_csrf") || "" },
    body: JSON.stringify({}),
  });
  if (!res.ok) return false;
  return true;
}

export async function api<T>(path: string, options: RequestInit = {}, auth = false): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (auth && options.method && !["GET", "HEAD"].includes(options.method.toUpperCase())) headers.set("X-CSRF-Token", cookie("gnk_csrf") || "");
  let res = await fetch(`${resolveApiBase()}${path}`, { ...options, headers, credentials: "include" });
  if (auth && res.status === 401) {
    const ok = await refreshAccessToken();
    if (ok) {
      const retryHeaders = new Headers(options.headers);
      retryHeaders.set("Content-Type", "application/json");
      if (options.method && !["GET", "HEAD"].includes(options.method.toUpperCase())) retryHeaders.set("X-CSRF-Token", cookie("gnk_csrf") || "");
      res = await fetch(`${resolveApiBase()}${path}`, { ...options, headers: retryHeaders, credentials: "include" });
    } else {
      clearTokens();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
      throw new Error("Session expired. Please login again.");
    }
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(errorDetail(data, res.statusText || "Request failed"));
  }
  return data as T;
}
