import type {
  ErrorCode,
  EvaluationMode,
  InputComposition,
  NovelType,
  ProviderConfigurationSource,
  ResultStatus,
  TaskStatus,
} from "@/api/contracts";


export interface DashboardTaskSummaryView {
  taskId: string;
  title: string;
  inputSummary: string;
  inputComposition: InputComposition;
  status: TaskStatus;
  resultStatus: ResultStatus;
  createdAt: string;
  resultAvailable: boolean;
}

export interface DashboardResultSummaryView {
  taskId: string;
  title: string;
  resultTime: string;
  overallScore: number;
  overallVerdict: string;
}

export interface DashboardSummaryView {
  recentTasks: DashboardTaskSummaryView[];
  activeTasks: DashboardTaskSummaryView[];
  recentResults: DashboardResultSummaryView[];
}

export interface TaskDetailView {
  taskId: string;
  title: string;
  inputSummary: string;
  inputComposition: InputComposition;
  hasChapters: boolean;
  hasOutline: boolean;
  evaluationMode: EvaluationMode;
  status: TaskStatus;
  resultStatus: ResultStatus;
  errorCode: ErrorCode | null;
  errorMessage: string | null;
  schemaVersion: string | null;
  promptVersion: string | null;
  rubricVersion: string | null;
  providerId: string | null;
  modelId: string | null;
  novelType: NovelType | null;
  typeClassificationConfidence: number | null;
  typeFallbackUsed: boolean | null;
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
  updatedAt: string;
  resultAvailable: boolean;
}

export interface AxisResultView {
  axisId: string;
  scoreBand: string;
  score: number;
  summary: string;
  reason: string;
  degradedByInput: boolean;
  riskTags: string[];
}

export interface PlatformCandidateView {
  name: string;
  weight: number;
  pitchQuote: string;
}

export interface OverallResultView {
  score: number;
  verdict: string;
  verdictSubQuote: string | null;
  summary: string;
  platformCandidates: PlatformCandidateView[];
  marketFit: string;
  strengths: string[];
  weaknesses: string[];
}

export interface TypeLensView {
  lensId: string;
  label: string;
  scoreBand: string;
  reason: string;
  confidence: number;
  degradedByInput: boolean;
  riskTags: string[];
}

export interface TypeAssessmentView {
  novelType: NovelType;
  classificationConfidence: number;
  fallbackUsed: boolean;
  summary: string;
  lenses: TypeLensView[];
}

export interface ResultBodyView {
  taskId: string;
  schemaVersion: string;
  promptVersion: string;
  rubricVersion: string;
  providerId: string;
  modelId: string;
  resultTime: string;
  axes: AxisResultView[];
  overall: OverallResultView;
  typeAssessment: TypeAssessmentView | null;
}

export interface ResultDetailView {
  taskId: string;
  state: "available" | "blocked" | "not_available";
  resultStatus: ResultStatus;
  resultTime: string | null;
  result: ResultBodyView | null;
  message: string | null;
}

export interface HistoryListView {
  items: DashboardTaskSummaryView[];
  meta: {
    nextCursor: string | null;
    limit: number;
  };
}

export interface ProviderStatusView {
  providerId: string;
  modelId: string;
  configured: boolean;
  configurationSource: ProviderConfigurationSource;
  canAnalyze: boolean;
  canConfigureFromUi: boolean;
  statusLabel: string;
  sourceLabel: string;
  blockingMessage: string | null;
}
