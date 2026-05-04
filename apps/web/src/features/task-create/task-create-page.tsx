"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { describeApiError } from "@/api/client";
import { useCreateTaskMutation, useProviderStatusQuery } from "@/api/hooks";
import {
  buildCreateTaskRequest,
  countTrimmedCharacters,
  deriveDraftSemantics,
  formatUploadSize,
  SubmissionValidationError,
  taskCreateFormSchema,
  type TaskCreateFormValues,
} from "@/features/task-create/submission";
import { routes } from "@/shared/config/routes";
import { getAnalysisModeLabel, getInputCompositionLabel } from "@/shared/lib/format";
import { cn } from "@/shared/lib/cn";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { ErrorState, PageIntro } from "@/shared/ui/states";


const acceptedFileTypes = ".txt,.md,.docx,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const analysisModeDescriptions = {
  long_opening_outline: "用于长篇项目的开篇与后续大纲联动评估，必须同时提交正文和大纲。",
  completed_fulltext: "用于已完结中短篇全文评估，只提交正文，不能附带大纲。",
} as const;
const analysisModeOptions: Array<{ label: string; value: TaskCreateFormValues["analysisMode"] }> = [
  { label: "长篇开篇 + 大纲", value: "long_opening_outline" },
  { label: "已完结全文", value: "completed_fulltext" },
];
const inputModeOptions: Array<{ label: string; value: TaskCreateFormValues["mode"] }> = [
  { label: "直接输入", value: "direct_input" },
  { label: "文件上传", value: "file_upload" },
];
type CheckerTone = "good" | "warn" | "bad" | "neutral";

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
      analysisMode: "long_opening_outline",
      title: "",
      chaptersText: "",
      outlineText: "",
    },
  });

  const mode = form.watch("mode");
  const analysisMode = form.watch("analysisMode");
  const title = form.watch("title");
  const chaptersText = form.watch("chaptersText");
  const outlineText = form.watch("outlineText");
  const draft = deriveDraftSemantics({
    mode,
    analysisMode,
    chaptersText,
    outlineText,
    chaptersFile,
    outlineFile,
  });
  const providerStatus = providerStatusQuery.data;
  const providerStatusUnavailable = providerStatusQuery.isError || (!providerStatusQuery.isPending && providerStatus === undefined);
  const providerBlocked = providerStatusQuery.isPending || providerStatusUnavailable || !providerStatus?.canAnalyze;
  const providerUnavailableOrBlocked = providerStatusUnavailable || Boolean(providerStatus && !providerStatus.canAnalyze);
  const providerBlockingMessage = providerStatusUnavailable
    ? "当前无法确认 provider 状态，请稍后重试。"
    : (providerStatus?.blockingMessage ?? "当前无 API，无法进行分析。");
  const outlineRequired = analysisMode === "long_opening_outline";
  const chaptersCharacterCount = countTrimmedCharacters(chaptersText);
  const outlineCharacterCount = countTrimmedCharacters(outlineText);
  const providerCheckerTone: CheckerTone = providerStatusQuery.isPending
    ? "neutral"
    : providerStatus?.canAnalyze
        ? "good"
        : "bad";
  const providerCheckerLabel = providerStatusQuery.isPending
    ? "Provider 状态读取中"
    : providerStatusUnavailable
      ? "Provider 状态未知"
      : (providerStatus?.statusLabel ?? "Provider 状态未知");
  const providerCheckerDetail = providerStatusQuery.isPending
    ? "正在确认是否可以创建评测任务。"
    : providerBlocked
      ? providerBlockingMessage
      : `${providerStatus?.sourceLabel ?? "已配置"}，可以创建评测任务。`;

  useEffect(() => {
    if (analysisMode !== "completed_fulltext") {
      return;
    }
    form.setValue("outlineText", "");
    form.clearErrors("outlineText");
    setOutlineFile(null);
  }, [analysisMode, form]);

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
        title="选择分析模式，提交小说材料。"
        description="长篇开篇模式需要正文与大纲；已完结全文模式只接收正文。系统会根据分析模式生成任务，并进入类型判断、LLM rubric 与类型 lens 结构化评价流程。"
        actions={<Button asLink href={routes.dashboard} variant="secondary">返回工作台</Button>}
      />

      {submitError ? (
        <ErrorState
          title="任务创建失败"
          description={submitError}
          action={<Button onClick={() => setSubmitError(null)} variant="secondary">清除提示</Button>}
        />
      ) : null}

      {providerUnavailableOrBlocked ? (
        <ErrorState
          title={providerStatusUnavailable ? "当前无法确认 provider 状态" : "当前无 API，无法进行分析"}
          description={providerStatusUnavailable
            ? providerBlockingMessage
            : `${providerBlockingMessage} 你仍可查看已有任务与结果，并可在侧边栏录入当前进程有效的运行时 Key。`}
        />
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-6 md:p-8">
          <SegmentedControl
            legend="分析模式"
            name="analysisMode"
            value={analysisMode}
            options={analysisModeOptions}
            onChange={(nextValue) => form.setValue("analysisMode", nextValue)}
          />

          <SegmentedControl
            legend="输入方式"
            name="inputMode"
            value={mode}
            options={inputModeOptions}
            className="mt-4"
            onChange={(nextValue) => form.setValue("mode", nextValue)}
          />
          <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
            {analysisModeDescriptions[analysisMode]}
          </p>

          <form className="mt-8 space-y-6" onSubmit={(event) => void form.handleSubmit(onSubmit)(event)}>
            <label className="block">
              <span className="text-sm font-semibold">任务标题</span>
              <input
                className="mt-2 w-full rounded-[10px] border border-[var(--line)] bg-white px-4 py-3 outline-none ring-0 transition focus:border-[var(--accent)]"
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
                    className="mt-2 min-h-56 w-full rounded-[10px] border border-[var(--line)] bg-white px-4 py-3 outline-none transition focus:border-[var(--accent)]"
                    placeholder={
                      analysisMode === "completed_fulltext"
                        ? "粘贴已完结全文，系统会按全文模式生成评测任务。"
                        : "粘贴需要评测的章节正文，系统会按当前输入生成评测任务。"
                    }
                    {...form.register("chaptersText")}
                  />
                  {form.formState.errors.chaptersText ? (
                    <p className="mt-2 text-sm text-[var(--bad)]">{form.formState.errors.chaptersText.message}</p>
                  ) : null}
                </label>
                {outlineRequired ? (
                  <label className="block">
                    <span className="text-sm font-semibold">大纲输入</span>
                    <textarea
                      className="mt-2 min-h-48 w-full rounded-[10px] border border-[var(--line)] bg-white px-4 py-3 outline-none transition focus:border-[var(--accent)]"
                      placeholder="粘贴大纲内容，帮助系统结合正文完成更完整的结构化评价。"
                      {...form.register("outlineText")}
                    />
                    {form.formState.errors.outlineText ? (
                      <p className="mt-2 text-sm text-[var(--bad)]">{form.formState.errors.outlineText.message}</p>
                    ) : null}
                  </label>
                ) : (
                  <div className="rounded-[10px] border border-dashed border-[var(--line)] bg-[var(--surface)] p-4 text-sm leading-7 text-[var(--muted)]">
                    当前模式只接受正文输入，大纲会被自动清空并禁用。
                  </div>
                )}
              </>
            ) : (
              <div className={outlineRequired ? "grid gap-5 md:grid-cols-2" : "grid gap-5"}>
                <label className="block rounded-[12px] border border-dashed border-[var(--line)] bg-white p-5">
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

                {outlineRequired ? (
                  <label className="block rounded-[12px] border border-dashed border-[var(--line)] bg-white p-5">
                    <span className="text-sm font-semibold">大纲文件</span>
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">长篇模式需要正文与大纲同时提交。</p>
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
                ) : (
                  <div className="rounded-[12px] border border-dashed border-[var(--line)] bg-[var(--surface)] p-5 text-sm leading-7 text-[var(--muted)]">
                    当前模式不接收大纲文件。
                  </div>
                )}
              </div>
            )}

            <div
              role="group"
              aria-labelledby="submit-checker-title"
              className="rounded-[12px] border border-[var(--line)] bg-white p-5"
            >
              <p id="submit-checker-title" className="text-xs tracking-[0.12em] text-[var(--muted)]">提交检查器</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge tone={draft.inputComposition ? "good" : "neutral"}>
                  {draft.inputComposition ? getInputCompositionLabel(draft.inputComposition) : "待输入"}
                </Badge>
                <Badge tone={draft.isReady ? "good" : "warn"}>
                  {getAnalysisModeLabel(analysisMode)}
                </Badge>
                <Badge tone={mode === "file_upload" ? "neutral" : "good"}>
                  {mode === "file_upload" ? "文件上传提交" : "直接输入提交"}
                </Badge>
                <Badge tone={draft.isReady ? "good" : "warn"}>{draft.isReady ? "输入已满足模式要求" : "仍需补齐输入"}</Badge>
                <Badge tone={providerCheckerTone}>{providerCheckerLabel}</Badge>
              </div>
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                <CheckerItem
                  label="任务标题"
                  value={title.trim() || "未填写"}
                  detail={title.trim() ? "标题已填写。" : "标题为空时无法提交。"}
                  tone={title.trim() ? "good" : "warn"}
                />
                <CheckerItem
                  label="Provider 状态"
                  value={providerCheckerLabel}
                  detail={providerCheckerDetail}
                  tone={providerCheckerTone}
                />
                {mode === "direct_input" ? (
                  <>
                    <CheckerItem
                      label="正文字符数"
                      value={`${chaptersCharacterCount} 字符`}
                      detail={chaptersCharacterCount > 0 ? "正文已输入。" : "仍需输入正文。"}
                      tone={chaptersCharacterCount > 0 ? "good" : "warn"}
                    />
                    {outlineRequired ? (
                      <CheckerItem
                        label="大纲字符数"
                        value={`${outlineCharacterCount} 字符`}
                        detail={outlineCharacterCount > 0 ? "大纲已输入。" : "长篇模式仍需输入大纲。"}
                        tone={outlineCharacterCount > 0 ? "good" : "warn"}
                      />
                    ) : null}
                  </>
                ) : (
                  <>
                    <CheckerItem
                      label="正文文件"
                      value={chaptersFile ? chaptersFile.name : "未选择正文文件"}
                      detail={chaptersFile ? formatUploadSize(chaptersFile.size) : "仍需选择正文文件。"}
                      tone={chaptersFile ? "good" : "warn"}
                    />
                    {outlineRequired ? (
                      <CheckerItem
                        label="大纲文件"
                        value={outlineFile ? outlineFile.name : "未选择大纲文件"}
                        detail={outlineFile ? formatUploadSize(outlineFile.size) : "长篇模式仍需选择大纲文件。"}
                        tone={outlineFile ? "good" : "warn"}
                      />
                    ) : null}
                  </>
                )}
              </div>
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
                    analysisMode: "long_opening_outline",
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
            <h2 className="section-title mt-3 text-2xl font-semibold">任务创建后会进入类型化评测流程</h2>
            <p className="mt-4 text-sm leading-7 text-[var(--muted)]">
              创建成功后会进入任务详情页，你可以先查看评测进度与类型识别，再进入结果页查看总体判断、类型评价与 8 轴结果。
            </p>
          </Card>
          <Card className="p-6">
            <p className="text-xs tracking-[0.12em] text-[var(--muted)]">提交要求</p>
            <h2 className="section-title mt-3 text-2xl font-semibold">提交前请确认输入材料完整</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-[var(--muted)]">
              <li>标题必填。</li>
              <li>长篇模式需要正文和大纲同时存在。</li>
              <li>全文模式只接受正文，不接收大纲。</li>
              <li>文件上传只接受 TXT / MD / DOCX。</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}

function SegmentedControl<TValue extends string>({
  legend,
  name,
  value,
  options,
  className,
  onChange,
}: {
  legend: string;
  name: string;
  value: TValue;
  options: Array<{ label: string; value: TValue }>;
  className?: string;
  onChange: (value: TValue) => void;
}) {
  return (
    <fieldset className={className}>
      <legend className="text-sm font-semibold">{legend}</legend>
      <div role="radiogroup" aria-label={legend} className="mt-2 flex flex-wrap gap-3">
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <label
              key={option.value}
              className={cn(
                "inline-flex cursor-pointer items-center justify-center rounded-[10px] border px-4 py-2 text-sm font-medium transition focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-[var(--accent)]",
                selected
                  ? "border-transparent bg-[var(--accent)] text-white shadow-[0_8px_18px_rgba(43,92,110,0.16)]"
                  : "border-[var(--line-strong)] bg-[var(--surface-strong)] text-[var(--foreground)] hover:border-[var(--accent)] hover:text-[var(--accent-strong)]"
              )}
            >
              <input
                className="sr-only"
                type="radio"
                name={name}
                value={option.value}
                checked={selected}
                onChange={() => onChange(option.value)}
              />
              <span>{option.label}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function CheckerItem({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail: string;
  tone?: CheckerTone;
}) {
  return (
    <section className="rounded-[10px] border border-[var(--line)] bg-[var(--surface)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.12em] text-[var(--muted)]">{label}</p>
          <p className="mt-2 break-all text-sm font-semibold">{value}</p>
        </div>
        <Badge tone={tone}>{tone === "good" ? "通过" : tone === "bad" ? "阻断" : tone === "warn" ? "待处理" : "信息"}</Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{detail}</p>
    </section>
  );
}
