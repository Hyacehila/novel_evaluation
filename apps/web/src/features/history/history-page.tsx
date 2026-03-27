"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

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
  const searchParams = useSearchParams();
  const skipDebouncedUrlSyncRef = useRef(false);
  const [draftQuery, setDraftQuery] = useState(searchParams.get("q") ?? "");
  const debouncedQuery = useDebouncedValue(draftQuery, 400);
  const currentQuery = searchParams.get("q") ?? "";
  const status = normalizeTaskStatus(searchParams.get("status"));
  const cursor = searchParams.get("cursor") ?? undefined;
  const limit = normalizeLimit(searchParams.get("limit"));

  useEffect(() => {
    setDraftQuery(currentQuery);
  }, [currentQuery]);

  useEffect(() => {
    if (skipDebouncedUrlSyncRef.current) {
      if (debouncedQuery === currentQuery) {
        skipDebouncedUrlSyncRef.current = false;
      }
      return;
    }

    if (debouncedQuery === currentQuery) {
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
    window.history.replaceState(null, "", queryString ? `${routes.history}?${queryString}` : routes.history);
  }, [currentQuery, debouncedQuery, searchParams]);

  const historyQuery = useHistoryQuery({
    q: currentQuery || undefined,
    status,
    cursor,
    limit,
  });

  function updateSearchParams(updater: (params: URLSearchParams) => void) {
    const next = new URLSearchParams(searchParams.toString());
    updater(next);
    const queryString = next.toString();
    window.history.pushState(null, "", queryString ? `${routes.history}?${queryString}` : routes.history);
  }

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="历史记录页"
        title="按任务回访历史评测记录与结果状态。"
        description="你可以按标题、状态和分页条件筛选历史任务，并继续查看可用的结构化评价结果。"
        actions={<Button asLink href={routes.newTask}>新建评测任务</Button>}
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
                skipDebouncedUrlSyncRef.current = true;
                setDraftQuery("");
                window.history.pushState(null, "", routes.history);
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
          description="当前无法读取历史任务列表。可以保留筛选条件后稍后重试。"
          action={<Button onClick={() => void historyQuery.refetch()}>重试读取</Button>}
        />
      ) : null}

      {historyQuery.data ? (
        <Card className="p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">历史评测记录</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">任务回访</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone="neutral">每页 {historyQuery.data.meta.limit} 条</Badge>
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
                      查看任务
                    </Button>
                    {item.resultAvailable ? (
                      <Button asLink href={routes.result(item.taskId)} prefetch={false}>查看结果</Button>
                    ) : null}
                  </div>
                </article>
              ))
            ) : (
              <EmptyState
                title="没有匹配的历史任务"
                description="当前筛选条件下没有匹配的评测任务。可以放宽关键字、切换状态，或返回第一页重新查看。"
              />
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                window.history.pushState(null, "", routes.history);
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
