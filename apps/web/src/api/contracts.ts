export type TaskStatus = "queued" | "processing" | "completed" | "failed";
export type ResultStatus = "available" | "not_available" | "blocked";
export type InputComposition = "chapters_outline" | "chapters_only" | "outline_only";
export type EvaluationMode = "full" | "degraded";
export type ProviderConfigurationSource = "missing" | "startup_env" | "runtime_memory";
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
  signingProbability: number;
  editorVerdict: string;
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

export interface PlatformRecommendationDto {
  name: string;
  percentage: number;
  reason: string;
}

export interface DetailedAnalysisDto {
  plot: string;
  character: string;
  pacing: string;
  worldBuilding: string;
}

export interface EvaluationResultDto {
  taskId: string;
  schemaVersion: string;
  promptVersion: string;
  rubricVersion: string;
  providerId: string;
  modelId: string;
  resultTime: string;
  signingProbability: number;
  commercialValue: number;
  writingQuality: number;
  innovationScore: number;
  strengths: string[];
  weaknesses: string[];
  platforms: PlatformRecommendationDto[];
  marketFit: string;
  editorVerdict: string;
  detailedAnalysis: DetailedAnalysisDto;
}

export interface EvaluationResultResourceDto {
  taskId: string;
  resultStatus: ResultStatus;
  resultTime: string | null;
  result: EvaluationResultDto | null;
  message: string | null;
}
