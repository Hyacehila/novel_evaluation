"use client";

import Link from "next/link";

import { useDashboardQuery } from "@/api/hooks";
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
import { EmptyState, ErrorState, KeyValueGrid, PageIntro } from "@/shared/ui/states";


export function DashboardPage() {
  const dashboardQuery = useDashboardQuery();

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="Dashboard"
        title="从任务排队到结果沉淀，全部收在一个入口里。"
        description="首页只负责摘要：最近任务、处理中任务和最近结果全部直接消费现有 API v0，不展示伪结果，也不改写后端状态语义。"
        actions={
          <>
            <Button asLink href={routes.newTask}>
              新建评测任务
            </Button>
            <Button asLink href={routes.history} variant="secondary">
              浏览历史记录
            </Button>
          </>
        }
      />

      {dashboardQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取 dashboard 摘要…</p>
        </Card>
      ) : null}

      {dashboardQuery.isError ? (
        <ErrorState
          title="首页摘要读取失败"
          description="当前无法获取 dashboard 数据。后端 API 仍可单独访问任务和结果页，可以稍后重试。"
          action={<Button onClick={() => void dashboardQuery.refetch()}>重试读取</Button>}
        />
      ) : null}

      {dashboardQuery.data ? (
        <>
          <KeyValueGrid
            items={[
              {
                label: "最近任务",
                value: `${dashboardQuery.data.recentTasks.length} 条`,
              },
              {
                label: "处理中任务",
                value: `${dashboardQuery.data.activeTasks.length} 条`,
              },
              {
                label: "最近结果",
                value: `${dashboardQuery.data.recentResults.length} 条`,
              },
              {
                label: "轮询策略",
                value: dashboardQuery.data.activeTasks.length > 0 ? "15 秒自动刷新" : "无活跃任务时停止",
                tone: "muted",
              },
            ]}
          />

          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Card className="p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Recent Tasks</p>
                  <h2 className="section-title mt-3 text-2xl font-semibold">最近任务</h2>
                </div>
                <Button asLink href={routes.history} variant="ghost">
                  查看全部
                </Button>
              </div>
              <div className="mt-6 space-y-4">
                {dashboardQuery.data.recentTasks.length > 0 ? (
                  dashboardQuery.data.recentTasks.map((task) => (
                    <Link
                      key={task.taskId}
                      href={routes.task(task.taskId)}
                      className="block rounded-[22px] border border-[var(--line)] bg-white/60 p-5 transition hover:-translate-y-0.5"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h3 className="text-lg font-semibold">{task.title}</h3>
                          <p className="mt-2 text-sm text-[var(--muted)]">{task.inputSummary}</p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge tone={statusTone(task.status)}>{getTaskStatusLabel(task.status)}</Badge>
                          <Badge tone={statusTone(task.resultStatus)}>{getResultStatusLabel(task.resultStatus)}</Badge>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-4 text-sm text-[var(--muted)]">
                        <span>{getInputCompositionLabel(task.inputComposition)}</span>
                        <span>{formatDateTime(task.createdAt)}</span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <EmptyState
                    title="还没有任务"
                    description="创建首个任务后，首页会在这里显示最近提交和运行状态。"
                    action={
                      <Button asLink href={routes.newTask}>
                        立即创建
                      </Button>
                    }
                  />
                )}
              </div>
            </Card>

            <div className="space-y-6">
              <Card className="p-6">
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Active Queue</p>
                <h2 className="section-title mt-3 text-2xl font-semibold">处理中任务</h2>
                <div className="mt-5 space-y-4">
                  {dashboardQuery.data.activeTasks.length > 0 ? (
                    dashboardQuery.data.activeTasks.map((task) => (
                      <Link
                        key={task.taskId}
                        href={routes.task(task.taskId)}
                        className="block rounded-[22px] border border-[var(--line)] bg-[rgba(255,255,255,0.6)] p-4"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="font-semibold">{task.title}</p>
                            <p className="mt-1 text-sm text-[var(--muted)]">{getTaskStatusLabel(task.status)}</p>
                          </div>
                          <Badge tone={statusTone(task.status)}>{getTaskStatusLabel(task.status)}</Badge>
                        </div>
                      </Link>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-[var(--muted)]">
                      当前没有 `queued/processing` 任务，dashboard 已停止主动轮询。
                    </p>
                  )}
                </div>
              </Card>

              <Card className="p-6">
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--muted)]">Recent Results</p>
                <h2 className="section-title mt-3 text-2xl font-semibold">最近结果</h2>
                <div className="mt-5 space-y-4">
                  {dashboardQuery.data.recentResults.length > 0 ? (
                    dashboardQuery.data.recentResults.map((result) => (
                      <Link
                        key={result.taskId}
                        href={routes.result(result.taskId)}
                        className="block rounded-[22px] border border-[var(--line)] bg-white/60 p-4 transition hover:-translate-y-0.5"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="font-semibold">{result.title}</p>
                            <p className="mt-1 text-sm text-[var(--muted)]">{formatDateTime(result.resultTime)}</p>
                          </div>
                          <span className="section-title text-3xl font-semibold">{result.signingProbability}</span>
                        </div>
                        <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{result.editorVerdict}</p>
                      </Link>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-[var(--muted)]">
                      目前还没有正式可展示的结果。只有 `available` 结果才会进入这个区块。
                    </p>
                  )}
                </div>
              </Card>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
