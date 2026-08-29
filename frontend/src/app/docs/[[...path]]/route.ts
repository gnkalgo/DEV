import { NextRequest } from "next/server";

import { backendInternalUrl } from "@/lib/backend-url";

async function proxyDocs(req: NextRequest, segments: string[]) {
  const sub = segments.length ? `/${segments.join("/")}` : "";
  const target = `${backendInternalUrl()}/docs${sub}${req.nextUrl.search}`;
  const res = await fetch(target, {
    cache: "no-store",
    headers: { accept: req.headers.get("accept") || "*/*" },
  });
  const headers = new Headers();
  const ct = res.headers.get("content-type");
  if (ct) headers.set("content-type", ct);
  return new Response(await res.arrayBuffer(), { status: res.status, headers });
}

export async function GET(
  req: NextRequest,
  ctx: { params: Promise<{ path?: string[] }> },
) {
  const { path } = await ctx.params;
  return proxyDocs(req, path || []);
}
