import { backendInternalUrl } from "@/lib/backend-url";

export async function GET() {
  const res = await fetch(`${backendInternalUrl()}/redoc`, { cache: "no-store" });
  const headers = new Headers();
  const ct = res.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  return new Response(await res.arrayBuffer(), { status: res.status, headers });
}
