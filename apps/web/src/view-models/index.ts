import type {
  DetailedAnalysisDto,
  ErrorCode,
  EvaluationMode,
  InputComposition,
  PlatformRecommendationDto,
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
  signingProbability: number;
  editorVerdict: string;
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
  createdAt: string;
  startedAt: string | null;
  completedAt: string | null;
  updatedAt: string;
  resultAvailable: boolean;
}

export interface ResultBodyView {
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
