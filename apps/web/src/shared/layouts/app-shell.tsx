"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { FormEvent, ReactNode } from "react";
import { useState } from "react";

import { describeApiError } from "@/api/client";
import { useConfigureRuntimeProviderKeyMutation, useProviderStatusQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";


const navItems = [
  { href: routes.dashboard, label: "工作台", description: "查看评测任务与结果摘要" },
  { href: routes.newTask, label: "新建评测任务", description: "提交正文或大纲发起评测" },
  { href: routes.history, label: "历史记录", description: "按标题、状态与分页回访任务" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const providerStatusQuery = useProviderStatusQuery();
  const configureMutation = useConfigureRuntimeProviderKeyMutation();
  const [runtimeApiKey, setRuntimeApiKey] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const providerStatus = providerStatusQuery.data;

  async function handleConfigure(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const apiKey = runtimeApiKey.trim();
    if (!apiKey) {
      setSubmitError("请输入 API Key。");
      return;
    }
    setSubmitError(null);
    try {
      await configureMutation.mutateAsync({ apiKey });
      setRuntimeApiKey("");
    } catch (error) {
      setSubmitError(describeApiError(error));
    }
  }

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
          <Card className="mt-6 p-5">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">Provider 状态</p>
            {providerStatusQuery.isPending ? (
              <div className="mt-3 space-y-3">
                <Badge tone="neutral">正在读取</Badge>
                <p className="text-sm leading-7 text-[var(--muted)]">正在读取当前 provider 配置状态。</p>
              </div>
            ) : providerStatusQuery.isError ? (
              <div className="mt-3 space-y-3">
                <Badge tone="bad">读取失败</Badge>
                <p className="text-sm leading-7 text-[var(--muted)]">当前无法读取 provider 状态，请稍后重试。</p>
                <Button type="button" variant="secondary" onClick={() => void providerStatusQuery.refetch()}>
                  重试读取
                </Button>
              </div>
            ) : providerStatus ? (
              <div className="mt-3 space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge tone={providerStatus.canAnalyze ? "good" : "warn"}>{providerStatus.statusLabel}</Badge>
                  <Badge tone={providerStatus.canAnalyze ? "neutral" : "warn"}>{providerStatus.sourceLabel}</Badge>
                </div>
                <p className="text-sm leading-7 text-[var(--muted)]">
                  {providerStatus.providerId} / {providerStatus.modelId}
                </p>
                {providerStatus.blockingMessage ? (
                  <p className="text-sm leading-7 text-[var(--muted)]">{providerStatus.blockingMessage}</p>
                ) : null}
                {providerStatus.canAnalyze ? (
                  <p className="text-sm leading-7 text-[var(--muted)]">
                    {providerStatus.configurationSource === "startup_env"
                      ? "当前 provider 由启动环境变量提供，UI 中不支持替换或清空。"
                      : "当前 provider 由运行时内存提供，仅当前 API 进程内有效，重启或热重载后失效。"}
                  </p>
                ) : null}
                {providerStatus.canConfigureFromUi ? (
                  <form className="space-y-3" onSubmit={(event) => void handleConfigure(event)}>
                    <label className="block">
                      <span className="text-sm font-semibold">运行时 API Key</span>
                      <input
                        type="password"
                        aria-label="运行时 API Key"
                        autoComplete="off"
                        value={runtimeApiKey}
                        onChange={(event) => setRuntimeApiKey(event.target.value)}
                        className="mt-2 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none ring-0 transition focus:border-[var(--accent)]"
                        placeholder="输入 DeepSeek API Key"
                      />
                    </label>
                    <p className="text-sm leading-7 text-[var(--muted)]">仅当前 API 进程内有效，重启或热重载后失效。</p>
                    {submitError ? <p className="text-sm text-[var(--bad)]">{submitError}</p> : null}
                    <Button type="submit" disabled={configureMutation.isPending}>
                      {configureMutation.isPending ? "正在录入运行时 Key…" : "录入运行时 Key"}
                    </Button>
                  </form>
                ) : null}
              </div>
            ) : null}
          </Card>
        </div>
      </aside>
      <main>{children}</main>
    </div>
  );
}
