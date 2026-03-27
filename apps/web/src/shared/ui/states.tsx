import type { ReactNode } from "react";

import { cn } from "@/shared/lib/cn";
import { Card } from "@/shared/ui/card";


export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <Card className="grain-card p-8 md:p-10">
      <p className="text-xs uppercase tracking-[0.28em] text-[var(--accent-strong)]">{eyebrow}</p>
      <div className="mt-4 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          <h1 className="section-title text-3xl font-semibold md:text-[2.6rem]">{title}</h1>
          <p className="mt-4 text-sm leading-7 text-[var(--muted)] md:text-base">{description}</p>
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </Card>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="p-8 text-center">
      <p className="text-sm tracking-[0.12em] text-[var(--muted)]">暂无内容</p>
      <h2 className="section-title mt-4 text-2xl font-semibold">{title}</h2>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[var(--muted)]">{description}</p>
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </Card>
  );
}

export function ErrorState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <Card className="border-[rgba(168,51,47,0.2)] bg-[rgba(255,244,242,0.86)] p-8">
      <p className="text-sm tracking-[0.12em] text-[var(--bad)]">出现问题</p>
      <h2 className="section-title mt-4 text-2xl font-semibold">{title}</h2>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--muted)]">{description}</p>
      {action ? <div className="mt-6 flex flex-wrap gap-3">{action}</div> : null}
    </Card>
  );
}

export function KeyValueGrid({
  items,
}: {
  items: Array<{ label: string; value: ReactNode; tone?: "default" | "muted" }>;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label} className="p-5">
          <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">{item.label}</p>
          <div
            className={cn(
              "mt-3 text-sm leading-7",
              item.tone === "muted" ? "text-[var(--muted)]" : "text-[var(--foreground)]"
            )}
          >
            {item.value}
          </div>
        </Card>
      ))}
    </div>
  );
}

export function ScoreMeter({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-[22px] border border-[var(--line)] bg-white/70 p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-[var(--muted)]">{label}</p>
        <span className="section-title text-2xl font-semibold">{value}</span>
      </div>
      <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-[rgba(31,26,23,0.08)]">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,#cf8a3f,#b4462a)]"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}
