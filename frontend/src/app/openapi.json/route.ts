import { backendInternalUrl } from "@/lib/backend-url";

export async function GET() {
  const res = await fetch(`${backendInternalUrl()}/openapi.json`, { cache: "no-store" });
  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("content-type") || "application/json" },
  });
}
