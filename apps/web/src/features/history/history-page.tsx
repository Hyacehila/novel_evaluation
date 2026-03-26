"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { TaskStatus } from "@/api/contracts";
import { useHistoryQuery } from "@/api/hooks";
import { useDebouncedValue } from "@/shared/hooks/use-debounced-value";
import { routes } from "@/shared/config/routes";
import {
  formatDateTime,
  getInputCompositionLabel,
  getResultStatusLabel,
  getTaskStatusLabel,
  statusTone,
} from "@/shared/lib/format";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { EmptyState, ErrorState, PageIntro } from "@/shared/ui/states";


const taskStatuses: TaskStatus[] = ["queued", "processing", "completed", "failed"];

export function HistoryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [draftQuery, setDraftQuery] = useState(searchParams.get("q") ?? "");
  const debouncedQuery = useDebouncedValue(draftQuery, 400);
  const status = normalizeTaskStatus(searchParams.get("status"));
  const cursor = searchParams.get("cursor") ?? undefined;
  const limit = normalizeLimit(searchParams.get("limit"));

  useEffect(() => {
    setDraftQuery(searchParams.get("q") ?? "");
  }, [searchParams]);

  useEffect(() => {
    if (debouncedQuery === (searchParams.get("q") ?? "")) {
      return;
    }
    const next = new URLSearchParams(searchParams.toString());
    if (debouncedQuery) {
      next.set("q", debouncedQuery);
    } else {
      next.delete("q");
    }
    next.delete("cursor");
    const queryString = next.toString();
    router.replace(queryString ? `${routes.history}?${queryString}` : routes.history);
  }, [debouncedQuery, router, searchParams]);

  const historyQuery = useHistoryQuery({
    q: debouncedQuery || undefined,
    status,
    cursor,
    limit,
  });

  function updateSearchParams(updater: (params: URLSearchParams) => void) {
    const next = new URLSearchParams(searchParams.toString());
    updater(next);
    const queryString = next.toString();
    router.push(queryString ? `${routes.history}?${queryString}` : routes.history);
  }

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="History"
        title="历史记录严格按任务组织，并完整透出 q / status / cursor / limit。"
        description="首期历史页不轮询，所有检索条件都写进 URL。结果入口只对 `available` 任务开放。"
        actions={<Button asLink href={routes.newTask}>新建任务</Button>}
      />

      <Card className="p-6">
        <div className="grid gap-4 md:grid-cols-[1fr_200px_140px_auto]">
          <label className="block">
            <span className="text-sm font-semibold">标题检索</span>
            <input
              className="mt-2 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
              placeholder="输入标题关键字"
              value={draftQuery}
              onChange={(event) => {
                setDraftQuery(event.target.value);
              }}
            />
          </label>

          <label className="block">
            <span className="text-sm font-semibold">任务状态</span>
            <select
              className="mt-2 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
              value={status ?? ""}
              onChange={(event) => {
                updateSearchParams((params) => {
                  if (event.target.value) {
                    params.set("status", event.target.value);
                  } else {
                    params.delete("status");
                  }
                  params.delete("cursor");
                });
              }}
            >
              <option value="">全部状态</option>
              {taskStatuses.map((item) => (
                <option key={item} value={item}>
                  {getTaskStatusLabel(item)}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-semibold">分页大小</span>
            <select
              className="mt-2 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
              value={String(limit)}
              onChange={(event) => {
                updateSearchParams((params) => {
                  params.set("limit", event.target.value);
                  params.delete("cursor");
                });
              }}
            >
              {[10, 20, 30, 50].map((item) => (
                <option key={item} value={String(item)}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <div className="flex items-end gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setDraftQuery("");
                router.push(routes.history);
              }}
            >
              清空筛选
            </Button>
          </div>
        </div>
      </Card>

      {historyQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取历史记录…</p>
        </Card>
      ) : null}

      {historyQuery.isError ? (
        <ErrorState
          title="历史记录读取失败"
          description="当前无法读取 history 列表。可以保留筛选条件后稍后重试。"
          action={<Button onClick={() => void historyQuery.refetch()}>重试读取</Button>}
        />
      ) : null}

      {historyQuery.data ? (
        <Card className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">History List</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">任务回访</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone="neutral">limit={historyQuery.data.meta.limit}</Badge>
              <Badge tone={cursor ? "warn" : "good"}>{cursor ? "已进入游标页" : "第一页"}</Badge>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {historyQuery.data.items.length > 0 ? (
              historyQuery.data.items.map((item) => (
                <article
                  key={item.taskId}
                  className="rounded-[22px] border border-[var(--line)] bg-white/65 p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold">{item.title}</h3>
                      <p className="mt-2 text-sm leading-7 text-[var(--muted)]">{item.inputSummary}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone={statusTone(item.status)}>{getTaskStatusLabel(item.status)}</Badge>
                      <Badge tone={statusTone(item.resultStatus)}>{getResultStatusLabel(item.resultStatus)}</Badge>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-4 text-sm text-[var(--muted)]">
                    <span>{getInputCompositionLabel(item.inputComposition)}</span>
                    <span>{formatDateTime(item.createdAt)}</span>
                    <span>{item.taskId}</span>
                  </div>
                  <div className="mt-5 flex flex-wrap gap-3">
                    <Button asLink href={routes.task(item.taskId)} variant="secondary">
                      打开任务
                    </Button>
                    {item.resultAvailable ? (
                      <Button asLink href={routes.result(item.taskId)}>打开结果</Button>
                    ) : null}
                  </div>
                </article>
              ))
            ) : (
              <EmptyState
                title="没有匹配的历史任务"
                description="当前筛选条件下没有返回任何任务。可以放宽关键字、切换状态，或返回第一页重新查看。"
              />
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                router.push(routes.history);
              }}
            >
              返回第一页
            </Button>
            <Button
              type="button"
              disabled={!historyQuery.data.meta.nextCursor}
              onClick={() => {
                if (!historyQuery.data?.meta.nextCursor) {
                  return;
                }
                updateSearchParams((params) => {
                  params.set("cursor", historyQuery.data.meta.nextCursor ?? "");
                });
              }}
            >
              下一页
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function normalizeTaskStatus(value: string | null): TaskStatus | undefined {
  if (!value) {
    return undefined;
  }
  return taskStatuses.includes(value as TaskStatus) ? (value as TaskStatus) : undefined;
}

function normalizeLimit(value: string | null) {
  const parsed = Number(value ?? "20");
  if (!Number.isFinite(parsed) || parsed < 1 || parsed > 50) {
    return 20;
  }
  return parsed;
}
