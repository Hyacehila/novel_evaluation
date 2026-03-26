"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createTaskJson,
  createTaskUpload,
  fetchDashboard,
  fetchHistory,
  fetchTask,
  fetchTaskResult,
  type HistoryQueryParams,
} from "@/api/client";
import type { CreateTaskSubmissionRequest } from "@/features/task-create/submission";
import { isTaskActive } from "@/shared/lib/format";


const queryKeys = {
  dashboard: ["dashboard-summary"] as const,
  task: (taskId: string) => ["task-detail", taskId] as const,
  result: (taskId: string) => ["task-result", taskId] as const,
  history: (params: HistoryQueryParams) =>
    ["history-list", params.q ?? "", params.status ?? "all", params.cursor ?? "", params.limit ?? 20] as const,
  historyPrefix: ["history-list"] as const,
};

export function useDashboardQuery() {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: fetchDashboard,
    refetchInterval(query) {
      const data = query.state.data;
      if (!data) {
        return false;
      }
      return data.activeTasks.some((task) => isTaskActive(task.status)) ? 15_000 : false;
    },
  });
}

export function useTaskQuery(taskId: string) {
  return useQuery({
    queryKey: queryKeys.task(taskId),
    queryFn: () => fetchTask(taskId),
    refetchInterval(query) {
      const data = query.state.data;
      if (!data) {
        return 5_000;
      }
      return isTaskActive(data.status) ? 5_000 : false;
    },
  });
}

export function useTaskResultQuery(taskId: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.result(taskId),
    queryFn: () => fetchTaskResult(taskId),
    enabled,
  });
}

export function useHistoryQuery(params: HistoryQueryParams) {
  return useQuery({
    queryKey: queryKeys.history(params),
    queryFn: () => fetchHistory(params),
  });
}

export function useCreateTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (request: CreateTaskSubmissionRequest) => {
      if (request.kind === "json") {
        return createTaskJson(request.payload);
      }
      return createTaskUpload(request.formData);
    },
    onSuccess(task) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
      void queryClient.invalidateQueries({ queryKey: queryKeys.historyPrefix });
      void queryClient.setQueryData(queryKeys.task(task.taskId), task);
    },
  });
}
