import type { ComponentProps } from "react";

import { cn } from "@/shared/lib/cn";


export function Card({ className, ...props }: ComponentProps<"section">) {
  return (
    <section
      {...props}
      className={cn(
        "rounded-[26px] border border-[var(--line)] bg-[var(--surface)] shadow-[var(--shadow)] backdrop-blur-sm",
        className
      )}
    />
  );
}
