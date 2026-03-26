import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";


type Tone = "good" | "warn" | "bad" | "neutral";

const toneClasses: Record<Tone, string> = {
  good: "border-[rgba(47,143,85,0.3)] bg-[rgba(47,143,85,0.12)] text-[var(--good)]",
  warn: "border-[rgba(191,123,24,0.28)] bg-[rgba(191,123,24,0.12)] text-[var(--warn)]",
  bad: "border-[rgba(168,51,47,0.28)] bg-[rgba(168,51,47,0.12)] text-[var(--bad)]",
  neutral: "border-[var(--line)] bg-white/50 text-[var(--muted)]",
};

export function Badge({
  children,
  className,
  tone = "neutral",
}: {
  children: ReactNode;
  className?: string;
  tone?: Tone;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-[0.08em]",
        toneClasses[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
