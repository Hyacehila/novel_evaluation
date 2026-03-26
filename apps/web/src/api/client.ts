import type {
  ApiEnvelope,
  ApiErrorObjectDto,
  CreateTaskJsonPayload,
  DashboardSummaryDto,
  EvaluationResultResourceDto,
  EvaluationTaskDto,
  HistoryListDto,
  TaskStatus,
} from "@/api/contracts";
import {
  mapDashboardSummary,
  mapHistoryList,
  mapResultDetail,
  mapTaskDetail,
} from "@/api/mappers";
import type {
  DashboardSummaryView,
  HistoryListView,
  ResultDetailView,
  TaskDetailView,
} from "@/view-models";


export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly details: Record<string, unknown> | null | undefined;
  readonly fieldErrors: Record<string, string> | null | undefined;
  readonly retryable: boolean | null | undefined;

  constructor(status: number, error: ApiErrorObjectDto | null, fallbackMessage: string) {
    super(error?.message ?? fallbackMessage);
    this.name = "ApiClientError";
    this.status = status;
    this.code = error?.code ?? null;
    this.details = error?.details;
    this.fieldErrors = error?.fieldErrors;
    this.retryable = error?.retryable;
  }
}

export type HistoryQueryParams = {
  q?: string;
  status?: TaskStatus;
  cursor?: string;
  limit?: number;
};

async function requestData<T>(path: string, init?: RequestInit) {
  const response = await fetch(path, {
    ...init,
    cache: "no-store",
  });
  const envelope = (await readEnvelope<T>(response)) as ApiEnvelope<T> | null;

  if (!response.ok) {
    throw new ApiClientError(response.status, envelope && !envelope.success ? envelope.error : null, "请求失败");
  }
  if (!envelope || !envelope.success) {
    throw new ApiClientError(response.status, envelope ? envelope.error : null, "响应格式非法");
  }
  return envelope.data;
}

async function readEnvelope<T>(response: Response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as ApiEnvelope<T>;
  } catch {
    return null;
  }
}

function buildHistoryPath(params: HistoryQueryParams) {
  const searchParams = new URLSearchParams();
  if (params.q) {
    searchParams.set("q", params.q);
  }
  if (params.status) {
    searchParams.set("status", params.status);
  }
  if (params.cursor) {
    searchParams.set("cursor", params.cursor);
  }
  if (params.limit) {
    searchParams.set("limit", String(params.limit));
  }
  const query = searchParams.toString();
  return query ? `/api/history?${query}` : "/api/history";
}

export async function fetchDashboard(): Promise<DashboardSummaryView> {
  const data = await requestData<DashboardSummaryDto>("/api/dashboard");
  return mapDashboardSummary(data);
}

export async function fetchTask(taskId: string): Promise<TaskDetailView> {
  const data = await requestData<EvaluationTaskDto>(`/api/tasks/${taskId}`);
  return mapTaskDetail(data);
}

export async function fetchTaskResult(taskId: string): Promise<ResultDetailView> {
  const data = await requestData<EvaluationResultResourceDto>(`/api/tasks/${taskId}/result`);
  return mapResultDetail(data);
}

export async function fetchHistory(params: HistoryQueryParams): Promise<HistoryListView> {
  const data = await requestData<HistoryListDto>(buildHistoryPath(params));
  return mapHistoryList(data);
}

export async function createTaskJson(payload: CreateTaskJsonPayload): Promise<TaskDetailView> {
  const data = await requestData<EvaluationTaskDto>("/api/tasks", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return mapTaskDetail(data);
}

export async function createTaskUpload(formData: FormData): Promise<TaskDetailView> {
  const data = await requestData<EvaluationTaskDto>("/api/tasks", {
    method: "POST",
    body: formData,
  });
  return mapTaskDetail(data);
}

export function describeApiError(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.code ? `${error.code}: ${error.message}` : error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}
