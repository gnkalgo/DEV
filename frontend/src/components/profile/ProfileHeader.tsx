"use client";

import Link from "next/link";

import { ProfilePhoto } from "@/components/profile/ProfilePhoto";
import type { Profile } from "@/services/profileService";

export function ProfileHeader({
  profile,
  onUpload,
  onRemove,
}: {
  profile: Profile;
  onUpload: (file: File) => Promise<void>;
  onRemove: () => Promise<void>;
}) {
  return (
    <section className="rounded border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <ProfilePhoto
            photoUrl={profile.profile_photo_url}
            displayName={profile.display_name}
            fullName={profile.full_name}
            onUpload={onUpload}
            onRemove={onRemove}
          />
          <div>
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">
              {profile.display_name || profile.full_name || profile.email}
            </h2>
            <p className="text-xs text-[var(--text-secondary)]">
              Client ID: <span className="font-mono text-[var(--text-primary)]">{profile.client_id}</span>
            </p>
            <p className="mt-1 text-[11px] text-[var(--text-secondary)]">
              {profile.email_verified ? "Email verified" : "Email not verified"}
              {profile.phone ? ` · ${profile.phone_verified ? "Mobile verified" : "Mobile not verified"}` : ""}
            </p>
          </div>
        </div>
        <Link
          href="/settings"
          className="rounded border border-[var(--border)] px-3 py-1.5 text-xs font-medium hover:bg-[var(--surface-secondary)]"
        >
          Edit Profile
        </Link>
      </div>
    </section>
  );
}
