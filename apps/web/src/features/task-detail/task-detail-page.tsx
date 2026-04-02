"use client";

import { useTaskQuery } from "@/api/hooks";
import { routes } from "@/shared/config/routes";
import {
  formatConfidence,
  formatDateTime,
  getEvaluationModeLabel,
  getInputCompositionLabel,
  getNovelTypeLabel,
  getResultStatusLabel,
  getTaskStatusLabel,
  isTaskActive,
  statusTone,
} from "@/shared/lib/format";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ErrorState, KeyValueGrid, PageIntro } from "@/shared/ui/states";


export function TaskDetailPage({ taskId }: { taskId: string }) {
  const taskQuery = useTaskQuery(taskId);

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="任务详情 / 状态页"
        title="查看评测任务状态、类型识别与结果入口。"
        description="任务完成前会持续刷新状态；类型判断会先写回任务页，结果可用后可继续进入结果详情页查看总体判断、类型评价与 8 轴结果。"
        actions={
          <>
            <Button asLink href={routes.history} variant="secondary">
              查看历史
            </Button>
            <Button asLink href={routes.newTask}>
              新建评测任务
            </Button>
          </>
        }
      />

      {taskQuery.isLoading ? (
        <Card className="p-8">
          <p className="text-sm text-[var(--muted)]">正在读取任务状态…</p>
        </Card>
      ) : null}

      {taskQuery.isError ? (
        <ErrorState
          title="任务不存在或读取失败"
          description="当前无法读取这个评测任务。请检查任务 ID 是否正确，或稍后重试。"
          action={<Button onClick={() => void taskQuery.refetch()}>重新读取</Button>}
        />
      ) : null}

      {taskQuery.data ? (
        <>
          <Card className="p-6 md:p-8">
            <div className="flex flex-wrap items-start justify-between gap-5">
              <div>
                <p className="text-xs tracking-[0.12em] text-[var(--muted)]">任务 ID</p>
                <h2 className="section-title mt-3 break-all text-2xl font-semibold">{taskQuery.data.taskId}</h2>
                <p className="mt-4 text-sm leading-7 text-[var(--muted)]">{taskQuery.data.inputSummary}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge tone={statusTone(taskQuery.data.status)}>{getTaskStatusLabel(taskQuery.data.status)}</Badge>
                <Badge tone={statusTone(taskQuery.data.resultStatus)}>{getResultStatusLabel(taskQuery.data.resultStatus)}</Badge>
              </div>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              {taskQuery.data.resultAvailable ? (
                <Button asLink href={routes.result(taskQuery.data.taskId)} prefetch={false}>
                  查看结果详情
                </Button>
              ) : null}
              <Button asLink href={routes.newTask} variant="secondary">
                再建一个评测任务
              </Button>
            </div>
          </Card>

          <KeyValueGrid
            items={[
              {
                label: "输入组成",
                value: getInputCompositionLabel(taskQuery.data.inputComposition),
              },
              {
                label: "评测模式",
                value: getEvaluationModeLabel(taskQuery.data.evaluationMode),
              },
              {
                label: "创建时间",
                value: formatDateTime(taskQuery.data.createdAt),
              },
              {
                label: "轮询策略",
                value: isTaskActive(taskQuery.data.status) ? "2 秒自动刷新任务状态" : "任务已结束，停止刷新",
                tone: "muted",
              },
            ]}
          />

          <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">类型识别</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">类型判断</h2>
              {taskQuery.data.novelType ? (
                <>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <Badge>{getNovelTypeLabel(taskQuery.data.novelType)}</Badge>
                    <Badge tone={taskQuery.data.typeFallbackUsed ? "warn" : "good"}>
                      {taskQuery.data.typeFallbackUsed ? "已触发兜底" : "直接命中类型"}
                    </Badge>
                  </div>
                  <dl className="mt-6 space-y-4 text-sm">
                    <MetadataRow label="识别置信度" value={formatConfidence(taskQuery.data.typeClassificationConfidence)} raw />
                    <MetadataRow label="类型状态" value={taskQuery.data.typeFallbackUsed ? "低置信回落到通用兜底" : "已锁定对应类型 lens"} raw />
                  </dl>
                </>
              ) : (
                <p className="mt-6 text-sm leading-7 text-[var(--muted)]">
                  类型识别仍在执行，任务页会在后台轮询时自动刷新。
                </p>
              )}
            </Card>

            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">任务进度</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">任务生命周期</h2>
              <dl className="mt-6 space-y-4 text-sm">
                <MetadataRow label="开始时间" value={taskQuery.data.startedAt} />
                <MetadataRow label="完成时间" value={taskQuery.data.completedAt} />
                <MetadataRow label="最后更新时间" value={taskQuery.data.updatedAt} />
              </dl>
            </Card>

            <Card className="p-6">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">版本信息</p>
              <h2 className="section-title mt-3 text-2xl font-semibold">运行元信息</h2>
              <dl className="mt-6 space-y-4 text-sm">
                <MetadataRow label="schemaVersion" value={taskQuery.data.schemaVersion} raw />
                <MetadataRow label="promptVersion" value={taskQuery.data.promptVersion} raw />
                <MetadataRow label="rubricVersion" value={taskQuery.data.rubricVersion} raw />
                <MetadataRow label="providerId" value={taskQuery.data.providerId} raw />
                <MetadataRow label="modelId" value={taskQuery.data.modelId} raw />
              </dl>
            </Card>
          </div>

          {taskQuery.data.status === "completed" && taskQuery.data.resultStatus === "blocked" ? (
            <ErrorState
              title="任务已结束，但结果被业务阻断"
              description={taskQuery.data.errorMessage ?? "当前输入未满足正式结果展示条件，因此不会展示正式评测正文。"}
              action={
                <Button asLink href={routes.newTask} variant="secondary">
                  修改输入后重试
                </Button>
              }
            />
          ) : null}

          {taskQuery.data.status === "failed" ? (
            <ErrorState
              title="任务执行失败"
              description={taskQuery.data.errorMessage ?? "评测流程出现技术故障，当前结果不可用。"}
              action={<Button asLink href={routes.newTask}>重新提交新任务</Button>}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function MetadataRow({
  label,
  value,
  raw = false,
}: {
  label: string;
  value: string | null;
  raw?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-[18px] border border-[var(--line)] bg-white/60 p-4">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="break-all">{raw ? value ?? "未设置" : formatDateTime(value)}</dd>
    </div>
  );
}
