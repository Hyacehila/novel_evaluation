"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Dispatch, FormEvent, ReactNode, SetStateAction } from "react";
import { useEffect, useState } from "react";

import { describeApiError } from "@/api/client";
import { useConfigureRuntimeProviderKeyMutation, useProviderStatusQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";


const navItems = [
  { href: routes.dashboard, label: "工作台", description: "查看任务进度、类型识别与结果摘要" },
  { href: routes.newTask, label: "新建评测任务", description: "提交正文或大纲发起类型化评测" },
  { href: routes.history, label: "历史记录", description: "按标题、状态与分页回访任务" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const providerStatusQuery = useProviderStatusQuery();
  const configureMutation = useConfigureRuntimeProviderKeyMutation();
  const [runtimeApiKey, setRuntimeApiKey] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [mobileProviderOpen, setMobileProviderOpen] = useState(false);
  const providerStatus = providerStatusQuery.data;
  const providerNeedsAttention = providerStatusQuery.isError || Boolean(providerStatus && !providerStatus.canAnalyze);
  const providerSummaryTone = providerStatusQuery.isPending
    ? "neutral"
    : providerStatusQuery.isError
      ? "bad"
      : providerStatus?.canAnalyze
        ? "good"
        : "warn";
  const providerSummaryLabel = providerStatusQuery.isPending
    ? "正在读取"
    : providerStatusQuery.isError
      ? "读取失败"
      : (providerStatus?.statusLabel ?? "状态未知");

  useEffect(() => {
    if (providerNeedsAttention) {
      setMobileProviderOpen(true);
    }
  }, [providerNeedsAttention]);

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
    <>
      <a href="#main-content" className="skip-link">跳到主内容</a>
      <div className="app-shell">
        <aside className="app-shell-sidebar" aria-label="全局导航与 provider 状态">
          <div className="app-shell-sidebar-inner">
          <div className="app-shell-brand-card rounded-[12px] border border-[var(--line)] bg-[var(--surface)] p-5 shadow-[var(--shadow)]">
            <p className="text-xs tracking-[0.16em] text-[var(--accent-strong)]">阶段一交付</p>
            <h1 className="section-title mt-4 text-2xl font-semibold">小说智能打分系统</h1>
            <p className="app-shell-desktop-copy mt-4 text-sm leading-7 text-[var(--muted)]">
              围绕小说正文与大纲输入，查看评测任务进度、类型识别、结构化评测结果与历史记录回访。
            </p>
          </div>
          <nav className="app-shell-nav mt-6 space-y-3" aria-label="主导航">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "app-shell-nav-link block rounded-[12px] border p-4 transition hover:border-[var(--accent)]",
                    active
                      ? "border-[rgba(47,102,114,0.28)] bg-[rgba(47,102,114,0.08)]"
                      : "border-[var(--line)] bg-white"
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold">{item.label}</span>
                    {active ? (
                      <span className="app-shell-active-chip rounded-[8px] bg-[var(--accent)] px-2 py-1 text-[10px] font-semibold text-white">
                        当前
                      </span>
                    ) : null}
                  </div>
                  <p className="app-shell-nav-description mt-2 text-sm leading-6 text-[var(--muted)]">{item.description}</p>
                </Link>
              );
            })}
          </nav>
          <Card className="app-shell-desktop-provider mt-6 p-5">
            <ProviderStatusPanel
              providerStatusQuery={providerStatusQuery}
              configureMutation={configureMutation}
              runtimeApiKey={runtimeApiKey}
              setRuntimeApiKey={setRuntimeApiKey}
              submitError={submitError}
              onConfigure={handleConfigure}
            />
          </Card>
          <Card className="app-shell-mobile-provider mt-3 p-3">
            <button
              type="button"
              className="flex w-full items-center justify-between gap-3 text-left"
              aria-expanded={mobileProviderOpen}
              aria-controls="mobile-provider-panel"
              onClick={() => setMobileProviderOpen((current) => !current)}
            >
              <span className="text-sm font-semibold">Provider 状态</span>
              <span className="flex flex-wrap items-center justify-end gap-2">
                <Badge tone={providerSummaryTone}>{providerSummaryLabel}</Badge>
                <span className="text-xs text-[var(--muted)]">{mobileProviderOpen ? "收起" : "展开"}</span>
              </span>
            </button>
            {mobileProviderOpen ? (
              <div id="mobile-provider-panel" className="mt-4 border-t border-[var(--line)] pt-4">
                <ProviderStatusPanel
                  providerStatusQuery={providerStatusQuery}
                  configureMutation={configureMutation}
                  runtimeApiKey={runtimeApiKey}
                  setRuntimeApiKey={setRuntimeApiKey}
                  submitError={submitError}
                  onConfigure={handleConfigure}
                />
              </div>
            ) : null}
          </Card>
        </div>
      </aside>
      <main id="main-content" tabIndex={-1}>{children}</main>
    </div>
    </>
  );
}

function ProviderStatusPanel({
  providerStatusQuery,
  configureMutation,
  runtimeApiKey,
  setRuntimeApiKey,
  submitError,
  onConfigure,
}: {
  providerStatusQuery: ReturnType<typeof useProviderStatusQuery>;
  configureMutation: ReturnType<typeof useConfigureRuntimeProviderKeyMutation>;
  runtimeApiKey: string;
  setRuntimeApiKey: Dispatch<SetStateAction<string>>;
  submitError: string | null;
  onConfigure: (event: FormEvent<HTMLFormElement>) => void | Promise<void>;
}) {
  const providerStatus = providerStatusQuery.data;

  return (
    <>
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
            <form className="space-y-3" onSubmit={(event) => void onConfigure(event)}>
              <label className="block">
                <span className="text-sm font-semibold">运行时 API Key</span>
                <input
                  type="password"
                  aria-label="运行时 API Key"
                  autoComplete="off"
                  value={runtimeApiKey}
                  onChange={(event) => setRuntimeApiKey(event.target.value)}
                  className="mt-2 w-full rounded-[10px] border border-[var(--line)] bg-white px-4 py-3 outline-none ring-0 transition focus:border-[var(--accent)]"
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
    </>
  );
}
