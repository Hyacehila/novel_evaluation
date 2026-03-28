"use client";

import Link from "next/link";

import { useDashboardQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import {
  formatDateTime,
  formatScore,
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
        eyebrow="工作台首页"
        title="集中查看评测任务进度与结构化评价结果。"
        description="这里汇总最近任务、评测进度与结果摘要，帮助你快速回访小说智能打分系统中的核心信息。"
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
          <p className="text-sm text-[var(--muted)]">正在读取工作台摘要…</p>
        </Card>
      ) : null}

      {dashboardQuery.isError ? (
        <ErrorState
          title="工作台摘要读取失败"
          description="当前无法获取最近任务与结果摘要。你可以稍后重试，或直接进入任务页和结果页继续查看。"
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
                label: "评测中任务",
                value: `${dashboardQuery.data.activeTasks.length} 条`,
              },
              {
                label: "最近结果摘要",
                value: `${dashboardQuery.data.recentResults.length} 条`,
              },
              {
                label: "轮询策略",
                value: dashboardQuery.data.activeTasks.length > 0 ? "15 秒自动刷新" : "当前无进行中的评测任务",
                tone: "muted",
              },
            ]}
          />

          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <Card className="p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs tracking-[0.12em] text-[var(--muted)]">最近评测任务</p>
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
                    title="还没有评测任务"
                    description="创建首个评测任务后，这里会显示最近提交的任务与当前进度。"
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
                <p className="text-xs tracking-[0.12em] text-[var(--muted)]">进行中的评测任务</p>
                <h2 className="section-title mt-3 text-2xl font-semibold">评测中任务</h2>
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
                      当前没有进行中的评测任务，工作台会在有新任务时继续更新。
                    </p>
                  )}
                </div>
              </Card>

              <Card className="p-6">
                <p className="text-xs tracking-[0.12em] text-[var(--muted)]">最近结果摘要</p>
                <h2 className="section-title mt-3 text-2xl font-semibold">最近结果</h2>
                <div className="mt-5 space-y-4">
                  {dashboardQuery.data.recentResults.length > 0 ? (
                    dashboardQuery.data.recentResults.map((result) => (
                      <Link
                        key={result.taskId}
                        href={routes.result(result.taskId)}
                        prefetch={false}
                        className="block rounded-[22px] border border-[var(--line)] bg-white/60 p-4 transition hover:-translate-y-0.5"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="font-semibold">{result.title}</p>
                            <p className="mt-1 text-sm text-[var(--muted)]">{formatDateTime(result.resultTime)}</p>
                          </div>
                          <span className="section-title text-3xl font-semibold">{formatScore(result.overallScore)}</span>
                        </div>
                        <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{result.overallVerdict}</p>
                      </Link>
                    ))
                  ) : (
                    <p className="text-sm leading-7 text-[var(--muted)]">
                      当前还没有可展示的结构化评价结果。结果生成后会出现在这个区块。
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
