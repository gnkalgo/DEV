import type { NextConfig } from "next";

const backendInternal =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${backendInternal}/:path*`,
      },
      { source: "/health", destination: `${backendInternal}/health` },
      { source: "/docs", destination: `${backendInternal}/docs` },
      { source: "/docs/:path*", destination: `${backendInternal}/docs/:path*` },
      { source: "/redoc", destination: `${backendInternal}/redoc` },
      { source: "/openapi.json", destination: `${backendInternal}/openapi.json` },
    ];
  },
};

export default nextConfig;
