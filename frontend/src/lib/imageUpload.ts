const ALLOWED_MIME = new Set(["image/png", "image/jpeg", "image/webp"]);
const ALLOWED_EXT = new Set(["png", "jpg", "jpeg", "webp"]);
const MAX_BYTES = 5 * 1024 * 1024;

export type ImageValidationResult =
  | { ok: true; file: File }
  | { ok: false; error: string };

export function validateImageFile(file: File): ImageValidationResult {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!ALLOWED_MIME.has(file.type) || !ALLOWED_EXT.has(ext)) {
    return { ok: false, error: "Use PNG, JPG, or WEBP (max 5 MB)." };
  }
  if (file.size > MAX_BYTES) {
    return { ok: false, error: "Image must be 5 MB or smaller." };
  }
  return { ok: true, file };
}

export function readImagePreview(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Could not read image"));
    reader.readAsDataURL(file);
  });
}
