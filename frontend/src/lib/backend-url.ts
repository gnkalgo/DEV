/** Internal Docker URL for server-side proxy to FastAPI. */
export function backendInternalUrl(): string {
  return process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
}
