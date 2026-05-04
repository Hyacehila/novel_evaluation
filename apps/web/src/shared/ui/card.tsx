import type { ComponentProps } from "react";

import { cn } from "@/shared/lib/cn";


export function Card({ className, ...props }: ComponentProps<"section">) {
  return (
    <section
      {...props}
      className={cn(
        "rounded-[12px] border border-[var(--line)] bg-[var(--surface)] shadow-[0_8px_24px_rgba(15,23,42,0.04)] backdrop-blur-sm",
        className
      )}
    />
  );
}
