import Image from "next/image";
import Link from "next/link";

type LogoProps = {
  href?: string;
  size?: number;
  showWordmark?: boolean;
  className?: string;
  variant?: "full" | "mark";
};

export function Logo({
  href = "/",
  size = 40,
  showWordmark = true,
  className = "",
  variant = "full",
}: LogoProps) {
  const mark = (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <Image
        src="/gnkalgo-brand.png"
        alt="GnKAlgo"
        width={size}
        height={size}
        className="shrink-0 rounded-md object-cover"
        priority
      />
      {showWordmark && variant === "full" && (
        <span className="leading-tight hidden sm:block">
          <span className="block text-sm font-semibold tracking-wide text-white">
            GNK <span className="text-[var(--accent)]">ALGO</span>
          </span>
          <span className="text-[9px] uppercase tracking-[0.16em] text-[var(--muted)]">
            Intelligence behind every trade
          </span>
        </span>
      )}
    </span>
  );

  if (!href) return mark;
  return (
    <Link href={href} className="inline-flex shrink-0">
      {mark}
    </Link>
  );
}
