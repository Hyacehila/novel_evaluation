import type {
  DashboardSummaryDto,
  EvaluationResultResourceDto,
  EvaluationTaskDto,
  EvaluationTaskSummaryDto,
  HistoryListDto,
  RecentResultSummaryDto,
} from "@/api/contracts";
import type {
  DashboardResultSummaryView,
  DashboardSummaryView,
  DashboardTaskSummaryView,
  HistoryListView,
  ResultDetailView,
  TaskDetailView,
} from "@/view-models";


export function mapTaskSummary(dto: EvaluationTaskSummaryDto): DashboardTaskSummaryView {
  return {
    taskId: dto.taskId,
    title: dto.title,
    inputSummary: dto.inputSummary,
    inputComposition: dto.inputComposition,
    status: dto.status,
    resultStatus: dto.resultStatus,
    createdAt: dto.createdAt,
    resultAvailable: dto.resultAvailable,
  };
}

export function mapRecentResult(dto: RecentResultSummaryDto): DashboardResultSummaryView {
  return {
    taskId: dto.taskId,
    title: dto.title,
    resultTime: dto.resultTime,
    signingProbability: dto.signingProbability,
    editorVerdict: dto.editorVerdict,
  };
}

export function mapDashboardSummary(dto: DashboardSummaryDto): DashboardSummaryView {
  return {
    recentTasks: dto.recentTasks.map(mapTaskSummary),
    activeTasks: dto.activeTasks.map(mapTaskSummary),
    recentResults: dto.recentResults.map(mapRecentResult),
  };
}

export function mapTaskDetail(dto: EvaluationTaskDto): TaskDetailView {
  return {
    taskId: dto.taskId,
    title: dto.title,
    inputSummary: dto.inputSummary,
    inputComposition: dto.inputComposition,
    hasChapters: dto.hasChapters,
    hasOutline: dto.hasOutline,
    evaluationMode: dto.evaluationMode,
    status: dto.status,
    resultStatus: dto.resultStatus,
    errorCode: dto.errorCode,
    errorMessage: dto.errorMessage,
    schemaVersion: dto.schemaVersion,
    promptVersion: dto.promptVersion,
    rubricVersion: dto.rubricVersion,
    providerId: dto.providerId,
    modelId: dto.modelId,
    createdAt: dto.createdAt,
    startedAt: dto.startedAt,
    completedAt: dto.completedAt,
    updatedAt: dto.updatedAt,
    resultAvailable: dto.resultAvailable,
  };
}

export function mapResultDetail(dto: EvaluationResultResourceDto): ResultDetailView {
  return {
    taskId: dto.taskId,
    state: dto.resultStatus,
    resultStatus: dto.resultStatus,
    resultTime: dto.resultTime,
    result: dto.result,
    message: dto.message,
  };
}

export function mapHistoryList(dto: HistoryListDto): HistoryListView {
  return {
    items: dto.items.map(mapTaskSummary),
    meta: {
      nextCursor: dto.meta.nextCursor ?? null,
      limit: dto.meta.limit ?? 20,
    },
  };
}
