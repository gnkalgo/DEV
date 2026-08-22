const MUTE_KEY = "gnkalgo.soundsMuted";

export function isSoundsMuted(): boolean {
  return window.localStorage.getItem(MUTE_KEY) === "1";
}

export function setSoundsMuted(muted: boolean): void {
  window.localStorage.setItem(MUTE_KEY, muted ? "1" : "0");
}

export function playUiSound(kind: "order" | "cancel"): void {
  if (isSoundsMuted()) return;
  const src = kind === "order" ? "/sounds/order-tick.wav" : "/sounds/cancel-tick.wav";
  const audio = new Audio(src);
  void audio.play().catch(() => undefined);
}
