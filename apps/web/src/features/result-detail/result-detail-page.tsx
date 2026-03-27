"use client";

import { useTaskQuery, useTaskResultQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import { formatDateTime, getResultStatusLabel, getTaskStatusLabel } from "@/shared/lib/format";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ErrorState, PageIntro, ScoreMeter } from "@/shared/ui/states";


export function ResultDetailPage({ taskId }: { taskId: string }) {
  const taskQuery = useTaskQuery(taskId);
  const resultQuery = useTaskResultQuery(taskId, Boolean(taskQuery.data));

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="结果详情页"
        title="查看正式的结构化评价结果。"
        description="当结果可用时，这里会展示签约概率、编辑结论、平台建议与详细分析；结果阻断或不可用时会明确提示原因。"
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

      {taskQuery.data && taskQuery.data.status !== "queued" && taskQuery.data.status !== "processing" && resultQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取结构化评价结果…</p>
        </Card>
      ) : null}

      {taskQuery.data && resultQuery.isError ? (
        <ErrorState
          title="结果读取失败"
          description="任务可能已经完成，但当前没有成功读取到结果资源。你可以稍后重试读取。"
          action={<Button onClick={() => void resultQuery.refetch()}>重试结果读取</Button>}
        />
      ) : null}

      {taskQuery.data && resultQuery.data && resultQuery.data.state !== "available" ? (
        <ErrorState
          title={resultQuery.data.state === "blocked" ? "结果已被阻断" : "结果当前不可用"}
          description={taskQuery.data.errorMessage ?? resultQuery.data.message ?? `当前结果状态为 ${getResultStatusLabel(resultQuery.data.resultStatus)}`}
          action={<Button asLink href={routes.task(taskId)} variant="secondary">查看任务状态</Button>}
        />
      ) : null}

      {taskQuery.data && resultQuery.data?.result ? (
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

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <ScoreMeter label="签约概率" value={resultQuery.data.result.signingProbability} />
            <ScoreMeter label="商业价值" value={resultQuery.data.result.commercialValue} />
            <ScoreMeter label="写作质量" value={resultQuery.data.result.writingQuality} />
            <ScoreMeter label="创新分" value={resultQuery.data.result.innovationScore} />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">编辑摘要</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">编辑结论与市场判断</h2>
              <div className="mt-5 space-y-5 text-sm leading-7">
                <AnalysisCard title="编辑结论" content={resultQuery.data.result.editorVerdict} />
                <AnalysisCard title="市场判断" content={resultQuery.data.result.marketFit} />
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

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">平台推荐</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">平台建议</h2>
              <div className="mt-5 space-y-4">
                {resultQuery.data.result.platforms.map((platform) => (
                  <div key={platform.name} className="rounded-[22px] border border-[var(--line)] bg-white/60 p-5">
                    <div className="flex items-center justify-between gap-4">
                      <h3 className="font-semibold">{platform.name}</h3>
                      <span className="section-title text-2xl font-semibold">{platform.percentage}%</span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{platform.reason}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">优势与弱点</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">优势与弱点</h2>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <ListCard title="优势" tone="good" items={resultQuery.data.result.strengths} />
                <ListCard title="弱点" tone="bad" items={resultQuery.data.result.weaknesses} />
              </div>
            </Card>
          </div>

          <Card className="p-6">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">详细分析</p>
            <h2 className="section-title mt-3 text-2xl font-semibold">详细分析</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <AnalysisCard title="剧情" content={resultQuery.data.result.detailedAnalysis.plot} />
              <AnalysisCard title="角色" content={resultQuery.data.result.detailedAnalysis.character} />
              <AnalysisCard title="节奏" content={resultQuery.data.result.detailedAnalysis.pacing} />
              <AnalysisCard title="世界观" content={resultQuery.data.result.detailedAnalysis.worldBuilding} />
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

function AnalysisCard({ title, content }: { title: string; content: string }) {
  return (
    <section className="rounded-[22px] border border-[var(--line)] bg-white/60 p-5">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{content}</p>
    </section>
  );
}

function ListCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "good" | "bad";
}) {
  const className =
    tone === "good"
      ? "border-[rgba(47,143,85,0.2)] bg-[rgba(47,143,85,0.08)] text-[var(--good)]"
      : "border-[rgba(168,51,47,0.2)] bg-[rgba(168,51,47,0.08)] text-[var(--bad)]";

  return (
    <section className={`rounded-[22px] border p-5 ${className}`}>
      <h3 className="font-semibold">{title}</h3>
      <ul className="mt-3 space-y-3 text-sm leading-7 text-[var(--foreground)]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
