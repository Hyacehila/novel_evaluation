import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { QueryObserverSuccessResult } from "@tanstack/react-query";

import { useTaskQuery } from "@/api/hooks";
import { TaskDetailPage } from "@/features/task-detail/task-detail-page";

vi.mock("next/link", async () => {
  const React = await import("react");

  return {
    default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => {
      void _prefetch;
      return React.createElement("a", { href, ...props }, children);
    },
  };
});

vi.mock("@/api/hooks", () => ({
  useTaskQuery: vi.fn(),
}));

const mockedUseTaskQuery = vi.mocked(useTaskQuery);
type TaskQueryResult = ReturnType<typeof useTaskQuery>;
type TaskQueryData = NonNullable<TaskQueryResult["data"]>;

function renderPage() {
  return renderToStaticMarkup(createElement(TaskDetailPage, { taskId: "task_degraded" }));
}

function buildSuccessQueryResult<TData>(data: TData): QueryObserverSuccessResult<TData, Error> {
  return {
    data,
    dataUpdatedAt: 0,
    error: null,
    errorUpdatedAt: 0,
    failureCount: 0,
    failureReason: null,
    errorUpdateCount: 0,
    isError: false,
    isFetched: true,
    isFetchedAfterMount: true,
    isFetching: false,
    isLoading: false,
    isPending: false,
    isLoadingError: false,
    isInitialLoading: false,
    isPaused: false,
    isPlaceholderData: false,
    isRefetchError: false,
    isRefetching: false,
    isStale: false,
    isSuccess: true,
    isEnabled: true,
    refetch: vi.fn(),
    status: "success",
    fetchStatus: "idle",
    promise: Promise.resolve(data),
    isIdle: false,
  } as QueryObserverSuccessResult<TData, Error>;
}

describe("task detail page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders degraded evaluation mode for joint input after formal screening downgrade", () => {
    const data: TaskQueryData = {
      taskId: "task_degraded",
      title: "联合输入降级任务",
      inputSummary: "已提交 1 章正文和 1 份大纲",
      inputComposition: "chapters_outline",
      hasChapters: true,
      hasOutline: true,
      evaluationMode: "degraded",
      status: "completed",
      resultStatus: "available",
      errorCode: null,
      errorMessage: null,
      schemaVersion: "1.0.0",
      promptVersion: "v2",
      rubricVersion: "rubric-v2",
      providerId: "provider-deepseek",
      modelId: "deepseek-chat",
      createdAt: "2026-03-28T10:00:00Z",
      startedAt: "2026-03-28T10:00:03Z",
      completedAt: "2026-03-28T10:00:08Z",
      updatedAt: "2026-03-28T10:00:08Z",
      resultAvailable: true,
    };
    mockedUseTaskQuery.mockReturnValue(buildSuccessQueryResult(data) as TaskQueryResult);

    const html = renderPage();

    expect(html).toContain("正文 + 大纲");
    expect(html).toContain("降级评测");
    expect(html).not.toContain("完整评测");
  });
});
