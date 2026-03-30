"use client";

import { useTaskQuery, useTaskResultQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import {
  formatDateTime,
  formatScore,
  getAxisLabel,
  getResultStatusLabel,
  getScoreBandLabel,
  getScoreBandTone,
  getTaskStatusLabel,
  isTaskActive,
} from "@/shared/lib/format";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ErrorState, PageIntro } from "@/shared/ui/states";

export function ResultDetailPage({ taskId }: { taskId: string }) {
  const taskQuery = useTaskQuery(taskId);
  const canReadResult = Boolean(taskQuery.data && !isTaskActive(taskQuery.data.status));
  const resultQuery = useTaskResultQuery(taskId, canReadResult);

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="结果详情页"
        title="查看正式的 8 轴结构化评价结果。"
        description="当结果可用时，这里会展示总体评分、总体结论、市场判断与 8 个 rubric 评价轴；结果阻断或不可用时会明确提示原因。"
        actions={<Button asLink href={routes.task(taskId)} variant="secondary">返回任务页</Button>}
      />

      {taskQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取任务状态…</p>
        </Card>
      ) : null}

      {taskQuery.isError ? (
        <ErrorState
          title="任务读取失败"
          description="结果详情页需要先确认任务状态。当前无法读取这个评测任务，请稍后重试。"
          action={<Button onClick={() => void taskQuery.refetch()}>重试任务读取</Button>}
        />
      ) : null}

      {taskQuery.data && (taskQuery.data.status === "queued" || taskQuery.data.status === "processing") ? (
        <Card className="p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">结果尚未生成</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">任务尚未进入可读结果状态</h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--muted)]">
                当前任务状态为 {getTaskStatusLabel(taskQuery.data.status)}。请回到任务页继续等待结果生成。
              </p>
            </div>
            <Badge tone="warn">{getTaskStatusLabel(taskQuery.data.status)}</Badge>
          </div>
          <div className="mt-6">
            <Button asLink href={routes.task(taskId)}>回到任务页继续轮询</Button>
          </div>
        </Card>
      ) : null}

      {taskQuery.data && canReadResult && resultQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取结构化评价结果…</p>
        </Card>
      ) : null}

      {taskQuery.data && canReadResult && resultQuery.isError ? (
        <ErrorState
          title="结果读取失败"
          description="任务可能已经完成，但当前没有成功读取到结果资源。你可以稍后重试读取。"
          action={<Button onClick={() => void resultQuery.refetch()}>重试结果读取</Button>}
        />
      ) : null}

      {taskQuery.data && canReadResult && resultQuery.data && resultQuery.data.state !== "available" ? (
        <ErrorState
          title={resultQuery.data.state === "blocked" ? "结果已被阻断" : "结果当前不可用"}
          description={taskQuery.data.errorMessage ?? resultQuery.data.message ?? `当前结果状态为 ${getResultStatusLabel(resultQuery.data.resultStatus)}`}
          action={<Button asLink href={routes.task(taskId)} variant="secondary">查看任务状态</Button>}
        />
      ) : null}

      {taskQuery.data && resultQuery.data?.state === "available" && resultQuery.data.result ? (
        <>
          <Card className="p-6 md:p-8">
            <div className="flex flex-wrap items-start justify-between gap-5">
              <div>
                <p className="text-xs tracking-[0.12em] text-[var(--muted)]">结构化评价结果</p>
                <h2 className="section-title mt-3 text-3xl font-semibold">{taskQuery.data.title}</h2>
                <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
                  结果生成时间：{formatDateTime(resultQuery.data.result.resultTime)}
                </p>
              </div>
              <Badge tone="good">{getResultStatusLabel(resultQuery.data.resultStatus)}</Badge>
            </div>
          </Card>

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">总体判断</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">总体结论与市场判断</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <MetricCard label="总体评分" value={formatScore(resultQuery.data.result.overall.score)} />
                <MetricCard label="平台候选数" value={`${resultQuery.data.result.overall.platformCandidates.length} 个`} />
              </div>
              <div className="mt-5 space-y-4">
                <AnalysisCard title="总体结论" content={resultQuery.data.result.overall.verdict} />
                <AnalysisCard title="总体摘要" content={resultQuery.data.result.overall.summary} />
                <AnalysisCard title="市场判断" content={resultQuery.data.result.overall.marketFit} />
              </div>
              <div className="mt-5">
                <p className="text-sm text-[var(--muted)]">平台候选</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {resultQuery.data.result.overall.platformCandidates.map((platform) => (
                    <Badge key={platform.name}>{platform.name}</Badge>
                  ))}
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">版本与模型</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">版本与模型</h2>
              <dl className="mt-5 space-y-4 text-sm">
                <MetadataRow label="schemaVersion" value={resultQuery.data.result.schemaVersion} />
                <MetadataRow label="promptVersion" value={resultQuery.data.result.promptVersion} />
                <MetadataRow label="rubricVersion" value={resultQuery.data.result.rubricVersion} />
                <MetadataRow label="providerId" value={resultQuery.data.result.providerId} />
                <MetadataRow label="modelId" value={resultQuery.data.result.modelId} />
              </dl>
            </Card>
          </div>

          <Card className="p-6">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">分轴结果</p>
            <h2 className="section-title mt-3 text-2xl font-semibold">{resultQuery.data.result.axes.length} 轴 rubric 结果</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {resultQuery.data.result.axes.map((axis) => (
                <AxisCard
                  key={axis.axisId}
                  axisId={axis.axisId}
                  score={axis.score}
                  scoreBand={axis.scoreBand}
                  summary={axis.summary}
                  reason={axis.reason}
                  degradedByInput={axis.degradedByInput}
                  riskTags={axis.riskTags}
                />
              ))}
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-[18px] border border-[var(--line)] bg-white/60 p-4">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="break-all">{value}</dd>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <section className="rounded-[22px] border border-[var(--line)] bg-white/60 p-5">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="section-title mt-3 text-3xl font-semibold">{value}</p>
    </section>
  );
}

function AnalysisCard({ title, content }: { title: string; content: string }) {
  return (
    <section className="rounded-[22px] border border-[var(--line)] bg-white/60 p-5">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{content}</p>
    </section>
  );
}

function AxisCard({
  axisId,
  score,
  scoreBand,
  summary,
  reason,
  degradedByInput,
  riskTags,
}: {
  axisId: string;
  score: number;
  scoreBand: string;
  summary: string;
  reason: string;
  degradedByInput: boolean;
  riskTags: string[];
}) {
  return (
    <section className="rounded-[22px] border border-[var(--line)] bg-white/60 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{getAxisLabel(axisId)}</h3>
          <p className="mt-2 text-sm text-[var(--muted)]">{summary}</p>
        </div>
        <p className="section-title text-2xl font-semibold">{formatScore(score)}</p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge tone={getScoreBandTone(scoreBand)}>{getScoreBandLabel(scoreBand)}</Badge>
        {degradedByInput ? <Badge tone="warn">输入降级</Badge> : null}
        {riskTags.map((riskTag) => (
          <Badge key={riskTag} tone="bad">{riskTag}</Badge>
        ))}
      </div>
      <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{reason}</p>
    </section>
  );
}
