"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { describeApiError } from "@/api/client";
import { useCreateTaskMutation, useProviderStatusQuery } from "@/api/hooks";
import {
  buildCreateTaskRequest,
  deriveDraftSemantics,
  SubmissionValidationError,
  taskCreateFormSchema,
  type TaskCreateFormValues,
} from "@/features/task-create/submission";
import { routes } from "@/shared/config/routes";
import { getEvaluationModeLabel, getInputCompositionLabel } from "@/shared/lib/format";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ErrorState, PageIntro } from "@/shared/ui/states";


const acceptedFileTypes = ".txt,.md,.docx,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export function TaskCreatePage() {
  const router = useRouter();
  const mutation = useCreateTaskMutation();
  const providerStatusQuery = useProviderStatusQuery();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [chaptersFile, setChaptersFile] = useState<File | null>(null);
  const [outlineFile, setOutlineFile] = useState<File | null>(null);
  const form = useForm<TaskCreateFormValues>({
    resolver: zodResolver(taskCreateFormSchema),
    defaultValues: {
      mode: "direct_input",
      title: "",
      chaptersText: "",
      outlineText: "",
    },
  });

  const mode = form.watch("mode");
  const title = form.watch("title");
  const chaptersText = form.watch("chaptersText");
  const outlineText = form.watch("outlineText");
  const draft = deriveDraftSemantics({
    mode,
    chaptersText,
    outlineText,
    chaptersFile,
    outlineFile,
  });
  const providerStatus = providerStatusQuery.data;
  const providerStatusUnavailable = providerStatusQuery.isError || providerStatus === undefined;
  const providerBlocked = providerStatusUnavailable || !providerStatus.canAnalyze;
  const providerBlockingMessage = providerStatusUnavailable
    ? "当前无法确认 provider 状态，请稍后重试。"
    : (providerStatus.blockingMessage ?? "当前无 API，无法进行分析。");

  async function onSubmit(values: TaskCreateFormValues) {
    setSubmitError(null);
    form.clearErrors();

    if (providerBlocked) {
      setSubmitError(providerBlockingMessage);
      return;
    }

    try {
      const request = buildCreateTaskRequest({
        values,
        chaptersFile,
        outlineFile,
      });
      const task = await mutation.mutateAsync(request);
      router.push(routes.task(task.taskId));
    } catch (error) {
      if (error instanceof SubmissionValidationError) {
        const field =
          error.field === "chaptersFile" || error.field === "outlineFile" ? "mode" : error.field;
        form.setError(field, {
          message: error.message,
        });
        setSubmitError(error.message);
        return;
      }
      setSubmitError(describeApiError(error));
    }
  }

  return (
    <div className="page-frame space-y-8">
      <PageIntro
        eyebrow="新建评测任务页"
        title="提交正文与大纲，发起小说结构化评测。"
        description="你可以直接粘贴正文和大纲，或上传稿件文件。系统会根据输入材料生成评测任务，并进入 LLM rubric 结构化评价流程。"
        actions={<Button asLink href={routes.dashboard} variant="secondary">返回工作台</Button>}
      />

      {submitError ? (
        <ErrorState
          title="任务创建失败"
          description={submitError}
          action={<Button onClick={() => setSubmitError(null)} variant="secondary">清除提示</Button>}
        />
      ) : null}

      {providerBlocked ? (
        <ErrorState
          title={providerStatusUnavailable ? "当前无法确认 provider 状态" : "当前无 API，无法进行分析"}
          description={providerStatusUnavailable
            ? providerBlockingMessage
            : `${providerBlockingMessage} 你仍可查看已有任务与结果，并可在侧边栏录入当前进程有效的运行时 Key。`}
        />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-6 md:p-8">
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant={mode === "direct_input" ? "primary" : "secondary"}
              onClick={() => form.setValue("mode", "direct_input")}
            >
              直接输入
            </Button>
            <Button
              type="button"
              variant={mode === "file_upload" ? "primary" : "secondary"}
              onClick={() => form.setValue("mode", "file_upload")}
            >
              文件上传
            </Button>
          </div>

          <form className="mt-8 space-y-6" onSubmit={(event) => void form.handleSubmit(onSubmit)(event)}>
            <label className="block">
              <span className="text-sm font-semibold">任务标题</span>
              <input
                className="mt-2 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none ring-0 transition focus:border-[var(--accent)]"
                placeholder="例如：女频修仙开篇评测"
                {...form.register("title")}
              />
              {form.formState.errors.title ? (
                <p className="mt-2 text-sm text-[var(--bad)]">{form.formState.errors.title.message}</p>
              ) : null}
            </label>

            {mode === "direct_input" ? (
              <>
                <label className="block">
                  <span className="text-sm font-semibold">正文输入</span>
                  <textarea
                    className="mt-2 min-h-56 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
                    placeholder="粘贴需要评测的章节正文，系统会按当前输入生成评测任务。"
                    {...form.register("chaptersText")}
                  />
                </label>
                <label className="block">
                  <span className="text-sm font-semibold">大纲输入</span>
                  <textarea
                    className="mt-2 min-h-48 w-full rounded-[18px] border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
                    placeholder="粘贴大纲内容，帮助系统结合正文完成更完整的结构化评价。"
                    {...form.register("outlineText")}
                  />
                  {form.formState.errors.chaptersText ? (
                    <p className="mt-2 text-sm text-[var(--bad)]">{form.formState.errors.chaptersText.message}</p>
                  ) : null}
                </label>
              </>
            ) : (
              <div className="grid gap-5 md:grid-cols-2">
                <label className="block rounded-[22px] border border-dashed border-[var(--line-strong)] bg-white/70 p-5">
                  <span className="text-sm font-semibold">正文文件</span>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">支持 TXT / MD / DOCX，单文件上限 10 MiB。</p>
                  <input
                    className="mt-4 block w-full text-sm"
                    type="file"
                    accept={acceptedFileTypes}
                    onChange={(event) => {
                      setChaptersFile(event.target.files?.[0] ?? null);
                    }}
                  />
                  <p className="mt-3 text-sm text-[var(--muted)]">{chaptersFile ? chaptersFile.name : "未选择正文文件"}</p>
                </label>

                <label className="block rounded-[22px] border border-dashed border-[var(--line-strong)] bg-white/70 p-5">
                  <span className="text-sm font-semibold">大纲文件</span>
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">可单独上传大纲文件，帮助系统判断剧情走向与后续展开。</p>
                  <input
                    className="mt-4 block w-full text-sm"
                    type="file"
                    accept={acceptedFileTypes}
                    onChange={(event) => {
                      setOutlineFile(event.target.files?.[0] ?? null);
                    }}
                  />
                  <p className="mt-3 text-sm text-[var(--muted)]">{outlineFile ? outlineFile.name : "未选择大纲文件"}</p>
                </label>
              </div>
            )}

            <div className="rounded-[24px] border border-[var(--line)] bg-[rgba(255,255,255,0.7)] p-5">
              <p className="text-xs tracking-[0.12em] text-[var(--muted)]">提交预览</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge tone={draft.inputComposition ? "good" : "neutral"}>
                  {draft.inputComposition ? getInputCompositionLabel(draft.inputComposition) : "待输入"}
                </Badge>
                <Badge tone={draft.evaluationMode === "degraded" ? "warn" : "good"}>
                  {draft.evaluationMode ? getEvaluationModeLabel(draft.evaluationMode) : "未确定模式"}
                </Badge>
                <Badge tone={mode === "file_upload" ? "neutral" : "good"}>
                  {mode === "file_upload" ? "文件上传提交" : "直接输入提交"}
                </Badge>
              </div>
              <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
                {title.trim() ? `当前任务标题：${title.trim()}` : "标题为空时无法提交。"}
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={mutation.isPending || providerBlocked || providerStatusQuery.isPending}>
                {mutation.isPending ? "正在创建评测任务…" : "创建评测任务"}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  form.reset({
                    mode: "direct_input",
                    title: "",
                    chaptersText: "",
                    outlineText: "",
                  });
                  setChaptersFile(null);
                  setOutlineFile(null);
                  setSubmitError(null);
                }}
              >
                清空表单
              </Button>
            </div>
          </form>
        </Card>

        <div className="space-y-6">
          <Card className="p-6">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">提交流程</p>
            <h2 className="section-title mt-3 text-2xl font-semibold">任务创建后会进入评测流程</h2>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
              创建成功后会进入任务详情页，你可以在其中查看评测进度、结果状态以及后续可读的结构化评价结果。
            </p>
          </Card>
          <Card className="p-6">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">提交要求</p>
            <h2 className="section-title mt-3 text-2xl font-semibold">提交前请确认输入材料完整</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--muted)]">
              <li>标题必填。</li>
              <li>正文和大纲至少存在一侧。</li>
              <li>文件上传只接受 TXT / MD / DOCX。</li>
              <li>单侧输入允许提交，但系统会进入降级评测模式。</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
