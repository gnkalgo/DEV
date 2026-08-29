"use client";

import { useRef, useState } from "react";

import { validateImageFile, readImagePreview } from "@/lib/imageUpload";

type ProfilePhotoProps = {
  photoUrl: string | null;
  displayName: string | null;
  fullName: string | null;
  onUpload: (file: File) => Promise<void>;
  onRemove: () => Promise<void>;
};

function initials(name: string | null, email: string) {
  const src = name || email;
  const parts = src.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return src.slice(0, 2).toUpperCase();
}

export function ProfilePhoto({
  photoUrl,
  displayName,
  fullName,
  onUpload,
  onRemove,
}: ProfilePhotoProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleFile(file: File) {
    const v = validateImageFile(file);
    if (!v.ok) {
      setError(v.error);
      return;
    }
    setError("");
    const p = await readImagePreview(v.file);
    setPreview(p);
    setLoading(true);
    try {
      await onUpload(v.file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setPreview(null);
    } finally {
      setLoading(false);
    }
  }

  const src = preview || photoUrl;
  const label = displayName || fullName || "User";

  return (
    <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-start">
      <div
        className="relative h-20 w-20 shrink-0 overflow-hidden rounded-full border border-[var(--border)] bg-[var(--surface-secondary)] flex items-center justify-center text-lg font-semibold text-[var(--accent)]"
        aria-label="Profile photo"
      >
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt="" className="h-full w-full object-cover" />
        ) : (
          initials(label, label)
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={loading}
          onClick={() => inputRef.current?.click()}
          className="rounded border border-[var(--border)] px-3 py-1.5 text-xs hover:bg-[var(--surface-secondary)]"
        >
          {loading ? "Uploading…" : "Change photo"}
        </button>
        {photoUrl && (
          <button
            type="button"
            onClick={async () => {
              setLoading(true);
              try {
                await onRemove();
                setPreview(null);
              } finally {
                setLoading(false);
              }
            }}
            className="rounded border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--negative)]"
          >
            Remove
          </button>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
            e.target.value = "";
          }}
        />
      </div>
      {error && <p className="text-xs text-[var(--negative)]">{error}</p>}
    </div>
  );
}
