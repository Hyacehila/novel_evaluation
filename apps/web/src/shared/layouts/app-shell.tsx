"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { routes } from "@/shared/config/routes";
import { cn } from "@/shared/lib/cn";


const navItems = [
  { href: routes.dashboard, label: "工作台", description: "任务与结果摘要" },
  { href: routes.newTask, label: "新建任务", description: "直接输入或上传文件" },
  { href: routes.history, label: "历史记录", description: "按 q/status/cursor 回访" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="border-b border-[var(--line)] bg-[rgba(255,248,240,0.75)] p-5 backdrop-blur-sm md:border-b-0 md:border-r md:p-7">
        <div className="sticky top-0">
          <div className="rounded-[28px] border border-[var(--line)] bg-[rgba(255,251,245,0.88)] p-6 shadow-[var(--shadow)]">
            <p className="text-xs uppercase tracking-[0.3em] text-[var(--accent-strong)]">Phase 1</p>
            <h1 className="section-title mt-4 text-3xl font-semibold">小说评测工作台</h1>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
              保持公开 API 冻结，在本地单机环境完成创建任务、轮询、结果阅读与历史回访。
            </p>
          </div>
          <nav className="mt-6 space-y-3">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "block rounded-[22px] border p-4 transition hover:-translate-y-0.5",
                    active
                      ? "border-[rgba(180,70,42,0.26)] bg-[rgba(180,70,42,0.12)]"
                      : "border-[var(--line)] bg-[rgba(255,255,255,0.58)] hover:border-[var(--line-strong)]"
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold">{item.label}</span>
                    {active ? (
                      <span className="rounded-full bg-[var(--accent)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-white">
                        Active
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>
      <main>{children}</main>
    </div>
  );
}
