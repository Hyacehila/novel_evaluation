"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { routes } from "@/shared/config/routes";
import { cn } from "@/shared/lib/cn";


const navItems = [
  { href: routes.dashboard, label: "工作台", description: "查看评测任务与结果摘要" },
  { href: routes.newTask, label: "新建评测任务", description: "提交正文或大纲发起评测" },
  { href: routes.history, label: "历史记录", description: "按标题、状态与分页回访任务" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="border-b border-[var(--line)] bg-[rgba(255,248,240,0.75)] p-5 backdrop-blur-sm md:border-b-0 md:border-r md:p-7">
        <div className="sticky top-0">
          <div className="rounded-[28px] border border-[var(--line)] bg-[rgba(255,251,245,0.88)] p-6 shadow-[var(--shadow)]">
            <p className="text-xs tracking-[0.16em] text-[var(--accent-strong)]">阶段一交付</p>
            <h1 className="section-title mt-4 text-3xl font-semibold">小说智能打分系统</h1>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
              围绕小说正文与大纲输入，查看评测任务进度、结构化评价结果与历史记录回访。
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
                      <span className="rounded-full bg-[var(--accent)] px-2 py-1 text-[10px] font-semibold tracking-[0.12em] text-white">
                        当前
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
