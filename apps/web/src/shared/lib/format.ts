import type {
  EvaluationMode,
  InputComposition,
  NovelType,
  ResultStatus,
  TaskStatus,
} from "@/api/contracts";

const axisLabels: Record<string, string> = {
  hookRetention: "开篇抓力",
  serialMomentum: "连载动能",
  characterDrive: "角色驱动",
  narrativeControl: "叙事控制",
  pacingPayoff: "节奏兑现",
  settingDifferentiation: "设定差异化",
  platformFit: "平台适配",
  commercialPotential: "商业潜力",
};

const scoreBandLabels: Record<string, string> = {
  "0": "不可评或严重失败",
  "1": "明显薄弱",
  "2": "勉强成立",
  "3": "合格",
  "4": "明显突出",
};

const novelTypeLabels: Record<NovelType, string> = {
  female_general: "女频通用",
  fantasy_upgrade: "玄幻升级",
  urban_reality: "都市现实",
  history_military: "历史军事",
  sci_fi_apocalypse: "科幻末世",
  suspense_horror: "悬疑惊悚",
  game_derivative: "游戏衍生",
  general_fallback: "通用兜底",
};

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

export function formatScore(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "未生成";
  }
  return `${value} 分`;
}

export function getAxisLabel(axisId: string) {
  return axisLabels[axisId] ?? axisId;
}

export function getScoreBandLabel(scoreBand: string) {
  return scoreBandLabels[scoreBand] ?? scoreBand;
}

export function getScoreBandTone(scoreBand: string) {
  switch (scoreBand) {
    case "0":
    case "1":
      return "bad" as const;
    case "2":
      return "warn" as const;
    case "4":
      return "good" as const;
    default:
      return "neutral" as const;
  }
}

export function getNovelTypeLabel(novelType: NovelType) {
  return novelTypeLabels[novelType] ?? novelType;
}

export function formatConfidence(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "未生成";
  }
  return `${Math.round(value * 100)}%`;
}
