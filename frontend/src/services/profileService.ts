import { api } from "@/lib/api";

export type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  display_name: string | null;
  phone: string | null;
  gender: string | null;
  date_of_birth: string | null;
  profile_photo_url: string | null;
  theme_preference: string;
  is_verified: boolean;
  mfa_enabled: boolean;
  client_id: string;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string;
  trading_segments: {
    code: string;
    name: string;
    status: string;
    icon: string;
  }[];
};

export async function fetchProfile(): Promise<Profile> {
  return api<Profile>("/api/v1/profile/", {}, true);
}

export async function updateProfile(data: Record<string, unknown>): Promise<Profile> {
  return api<Profile>("/api/v1/profile/", {
    method: "PATCH",
    body: JSON.stringify(data),
  }, true);
}

export async function uploadProfilePhoto(file: File): Promise<Profile> {
  const form = new FormData();
  form.append("file", file);
  const token = typeof window !== "undefined" ? localStorage.getItem("gnk_access") : null;
  const base = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "";
  const res = await fetch(`${base}/api/v1/profile/photo`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data as Profile;
}

export async function removeProfilePhoto(): Promise<Profile> {
  return api<Profile>("/api/v1/profile/photo", { method: "DELETE" }, true);
}
