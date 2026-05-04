import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";


type Tone = "good" | "warn" | "bad" | "neutral";

const toneClasses: Record<Tone, string> = {
  good: "border-[rgba(36,123,85,0.24)] bg-[rgba(36,123,85,0.09)] text-[var(--good)]",
  warn: "border-[rgba(174,111,18,0.24)] bg-[rgba(174,111,18,0.1)] text-[var(--warn)]",
  bad: "border-[rgba(184,55,65,0.24)] bg-[rgba(184,55,65,0.09)] text-[var(--bad)]",
  neutral: "border-[var(--line)] bg-white text-[var(--muted)]",
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
        "inline-flex items-center rounded-[8px] border px-2.5 py-1 text-xs font-semibold",
        toneClasses[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
