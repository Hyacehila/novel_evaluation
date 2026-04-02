import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { QueryObserverSuccessResult } from "@tanstack/react-query";

import { useDashboardQuery } from "@/api/hooks";
import { DashboardPage } from "@/features/dashboard/dashboard-page";

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
  useDashboardQuery: vi.fn(),
}));

const mockedUseDashboardQuery = vi.mocked(useDashboardQuery);
type DashboardQueryResult = ReturnType<typeof useDashboardQuery>;
type DashboardQueryData = NonNullable<DashboardQueryResult["data"]>;

function renderPage() {
  return renderToStaticMarkup(createElement(DashboardPage));
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

describe("dashboard page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders recent result summaries with overall score and verdict", () => {
    const data: DashboardQueryData = {
      recentTasks: [],
      activeTasks: [],
      recentResults: [
        {
          taskId: "task_available",
          title: "测试稿件",
          resultTime: "2026-03-28T10:00:08Z",
          overallScore: 78,
          overallVerdict: "建议继续观察并进入样章复核。",
        },
      ],
    };
    mockedUseDashboardQuery.mockReturnValue(buildSuccessQueryResult(data) as DashboardQueryResult);

    const html = renderPage();

    expect(html).toContain("最近结果");
    expect(html).toContain("测试稿件");
    expect(html).toContain("78 分");
    expect(html).toContain("建议继续观察并进入样章复核。");
    expect(html).toContain('/tasks/task_available/result');
  });

  it("renders the empty-state copy when recent results are unavailable", () => {
    const data: DashboardQueryData = {
      recentTasks: [],
      activeTasks: [],
      recentResults: [],
    };
    mockedUseDashboardQuery.mockReturnValue(buildSuccessQueryResult(data) as DashboardQueryResult);

    const html = renderPage();

    expect(html).toContain("当前还没有可展示的评测结果摘要。结果生成后会在这里展示总体判断与最新结论。");
  });
});
