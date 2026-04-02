export type TaskStatus = "queued" | "processing" | "completed" | "failed";
export type ResultStatus = "available" | "not_available" | "blocked";
export type InputComposition = "chapters_outline" | "chapters_only" | "outline_only";
export type EvaluationMode = "full" | "degraded";
export type ProviderConfigurationSource = "missing" | "startup_env" | "runtime_memory";
export type NovelType =
  | "female_general"
  | "fantasy_upgrade"
  | "urban_reality"
  | "history_military"
  | "sci_fi_apocalypse"
  | "suspense_horror"
  | "game_derivative"
  | "general_fallback";
export type ErrorCode = string;

export interface MetaDataDto {
  nextCursor?: string | null;
  limit?: number | null;
}

export interface ApiSuccessEnvelope<T> {
  success: true;
  data: T;
  meta?: MetaDataDto;
}

export interface ApiErrorObjectDto {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown> | null;
  fieldErrors?: Record<string, string> | null;
  retryable?: boolean | null;
}

export interface ApiErrorEnvelope {
  success: false;
  error: ApiErrorObjectDto;
}

export type ApiEnvelope<T> = ApiSuccessEnvelope<T> | ApiErrorEnvelope;

export interface ManuscriptChapterPayload {
  title: string;
  content: string;
}

export interface ManuscriptOutlinePayload {
  content: string;
}

export interface CreateTaskJsonPayload {
  title: string;
  chapters?: ManuscriptChapterPayload[];
  outline?: ManuscriptOutlinePayload;
  sourceType: "direct_input";
}

export interface ConfigureRuntimeKeyPayload {
  apiKey: string;
}

export interface ProviderStatusDto {
  providerId: string;
  modelId: string;
  configured: boolean;
  configurationSource: ProviderConfigurationSource;
  canAnalyze: boolean;
  canConfigureFromUi: boolean;
}

export interface EvaluationTaskDto {
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

export interface EvaluationTaskSummaryDto {
  taskId: string;
  title: string;
  inputSummary: string;
  inputComposition: InputComposition;
  status: TaskStatus;
  resultStatus: ResultStatus;
  createdAt: string;
  resultAvailable: boolean;
}

export interface RecentResultSummaryDto {
  taskId: string;
  title: string;
  resultTime: string;
  overallScore: number;
  overallVerdict: string;
}

export interface DashboardSummaryDto {
  recentTasks: EvaluationTaskSummaryDto[];
  activeTasks: EvaluationTaskSummaryDto[];
  recentResults: RecentResultSummaryDto[];
}

export interface HistoryListDto {
  items: EvaluationTaskSummaryDto[];
  meta: MetaDataDto;
}

export interface AxisResultDto {
  axisId: string;
  scoreBand: string;
  score: number;
  summary: string;
  reason: string;
  degradedByInput: boolean;
  riskTags: string[];
}

export interface PlatformCandidateDto {
  name: string;
  weight: number;
  pitchQuote: string;
}

export interface OverallResultDto {
  score: number;
  verdict: string;
  verdictSubQuote: string | null;
  summary: string;
  platformCandidates: PlatformCandidateDto[];
  marketFit: string;
  strengths: string[];
  weaknesses: string[];
}

export interface TypeLensDto {
  lensId: string;
  label: string;
  scoreBand: string;
  reason: string;
  confidence: number;
  degradedByInput: boolean;
  riskTags: string[];
}

export interface TypeAssessmentDto {
  novelType: NovelType;
  classificationConfidence: number;
  fallbackUsed: boolean;
  summary: string;
  lenses: TypeLensDto[];
}

export interface EvaluationResultDto {
  taskId: string;
  schemaVersion: string;
  promptVersion: string;
  rubricVersion: string;
  providerId: string;
  modelId: string;
  resultTime: string;
  axes: AxisResultDto[];
  overall: OverallResultDto;
  typeAssessment: TypeAssessmentDto | null;
}

export interface EvaluationResultResourceDto {
  taskId: string;
  resultStatus: ResultStatus;
  resultTime: string | null;
  result: EvaluationResultDto | null;
  message: string | null;
}
