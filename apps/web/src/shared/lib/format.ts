import type {
  EvaluationMode,
  InputComposition,
  ResultStatus,
  TaskStatus,
} from "@/api/contracts";


export function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "未生成";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function getInputCompositionLabel(value: InputComposition) {
  switch (value) {
    case "chapters_outline":
      return "正文 + 大纲";
    case "chapters_only":
      return "仅正文";
    case "outline_only":
      return "仅大纲";
  }
}

export function getEvaluationModeLabel(value: EvaluationMode) {
  return value === "full" ? "完整评测" : "降级评测";
}

export function getTaskStatusLabel(value: TaskStatus) {
  switch (value) {
    case "queued":
      return "排队中";
    case "processing":
      return "评测中";
    case "completed":
      return "已完成";
    case "failed":
      return "任务失败";
  }
}

export function getResultStatusLabel(value: ResultStatus) {
  switch (value) {
    case "available":
      return "结果可用";
    case "not_available":
      return "结果不可用";
    case "blocked":
      return "结果被阻断";
  }
}

export function isTaskActive(status: TaskStatus) {
  return status === "queued" || status === "processing";
}

export function isTaskTerminal(status: TaskStatus) {
  return status === "completed" || status === "failed";
}

export function statusTone(status: TaskStatus | ResultStatus) {
  switch (status) {
    case "completed":
    case "available":
      return "good";
    case "failed":
    case "blocked":
      return "bad";
    default:
      return "warn";
  }
}
