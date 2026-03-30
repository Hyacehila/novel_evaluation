import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { QueryObserverSuccessResult } from "@tanstack/react-query";

import { useTaskQuery, useTaskResultQuery } from "@/api/hooks";
import { ResultDetailPage } from "@/features/result-detail/result-detail-page";

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
  useTaskResultQuery: vi.fn(),
}));

const mockedUseTaskQuery = vi.mocked(useTaskQuery);
const mockedUseTaskResultQuery = vi.mocked(useTaskResultQuery);
type TaskQueryResult = ReturnType<typeof useTaskQuery>;
type TaskResultQueryResult = ReturnType<typeof useTaskResultQuery>;
type TaskQueryData = NonNullable<TaskQueryResult["data"]>;
type TaskResultQueryData = NonNullable<TaskResultQueryResult["data"]>;

function renderPage() {
  return renderToStaticMarkup(createElement(ResultDetailPage, { taskId: "task_available" }));
}

function buildTaskQueryData(): TaskQueryData {
  return {
    taskId: "task_available",
    title: "测试稿件",
    inputSummary: "正文 + 大纲",
    inputComposition: "chapters_outline",
    hasChapters: true,
    hasOutline: true,
    evaluationMode: "full",
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

function buildAvailableResultBody(): NonNullable<TaskResultQueryData["result"]> {
  return {
    taskId: "task_available",
    schemaVersion: "1.0.0",
    promptVersion: "v2",
    rubricVersion: "rubric-v2",
    providerId: "provider-deepseek",
    modelId: "deepseek-chat",
    resultTime: "2026-03-28T10:00:08Z",
    axes: [
      {
        axisId: "hookRetention",
        scoreBand: "3",
        score: 75,
        summary: "开篇冲突建立较快，留读动力明确。",
        reason: "主角在首章就被卷入宗门危机，读者能快速感知目标与压力。",
        degradedByInput: false,
        riskTags: [],
      },
      {
        axisId: "characterDrive",
        scoreBand: "2",
        score: 55,
        summary: "角色目标已经出现，但情绪牵引还不够稳定。",
        reason: "主角动机明确，不过人物关系张力还需要更持续的兑现。",
        degradedByInput: true,
        riskTags: [],
      },
    ],
    overall: {
      score: 72,
      verdict: "建议继续观察并进入样章复核。",
      verdictSubQuote: "情感密度与节奏控制更贴合深耕慢热读者的平台气质。",
      summary: "整体完成度稳定，具备进一步评估价值。",
      platformCandidates: [
        { name: "女频平台 A", weight: 70, pitchQuote: "情感流向与平台核心读者群体高度匹配。" },
        { name: "女频平台 B", weight: 30, pitchQuote: "题材定位次级适配，可作为备选投放渠道。" },
      ],
      marketFit: "当前题材与节奏更贴合女频平台 A 的读者预期。",
      strengths: ["开篇抓力稳定"],
      weaknesses: ["长线兑现待验证"],
    },
  };
}

function mockTaskQuery() {
  mockedUseTaskQuery.mockReturnValue(buildSuccessQueryResult(buildTaskQueryData()) as TaskQueryResult);
}

function mockAvailableResultQuery() {
  const data: TaskResultQueryData = {
    taskId: "task_available",
    state: "available",
    resultStatus: "available",
    resultTime: "2026-03-28T10:00:08Z",
    result: buildAvailableResultBody(),
    message: null,
  };

  mockedUseTaskResultQuery.mockReturnValue(buildSuccessQueryResult(data) as TaskResultQueryResult);
}

describe("result detail page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders overall content instead of legacy four-score sections", () => {
    mockTaskQuery();
    mockAvailableResultQuery();

    const html = renderPage();

    expect(html).toContain("结构化评价结果");
    expect(html).toContain("测试稿件");
    expect(html).toContain("总体评分");
    expect(html).toContain("72 分");
    expect(html).toContain("建议继续观察并进入样章复核。");
    expect(html).toContain("整体完成度稳定，具备进一步评估价值。");
    expect(html).toContain("当前题材与节奏更贴合女频平台 A 的读者预期。");
    expect(html).toContain("女频平台 A");
    expect(html).not.toContain("签约概率");
    expect(html).not.toContain("商业价值");
    expect(html).not.toContain("写作质量");
    expect(html).not.toContain("创新分");
    expect(html).not.toContain("平台建议");
    expect(html).not.toContain("详细分析");
    expect(html).not.toContain("优势与弱点");
  });

  it("renders axis cards from the axes array", () => {
    mockTaskQuery();
    mockAvailableResultQuery();

    const html = renderPage();

    expect(html).toContain("开篇抓力");
    expect(html).toContain("角色驱动");
    expect(html).toContain("2 轴 rubric 结果");
    expect(html).toContain("75 分");
    expect(html).toContain("55 分");
    expect(html).toContain("合格");
    expect(html).toContain("勉强成立");
    expect(html).toContain("开篇冲突建立较快，留读动力明确。");
    expect(html).toContain("主角在首章就被卷入宗门危机");
    expect(html).toContain("输入降级");
  });

  it("keeps blocked results out of the formal result body", () => {
    mockTaskQuery();
    const data: TaskResultQueryData = {
      taskId: "task_available",
      state: "blocked",
      resultStatus: "blocked",
      resultTime: null,
      result: null,
      message: "结果未满足正式展示条件",
    };
    mockedUseTaskResultQuery.mockReturnValue(buildSuccessQueryResult(data) as TaskResultQueryResult);

    const html = renderPage();

    expect(html).toContain("结果已被阻断");
    expect(html).toContain("结果未满足正式展示条件");
    expect(html).not.toContain("72 分");
    expect(html).not.toContain("开篇抓力");
    expect(html).not.toContain("签约概率");
  });

  it("does not render the formal body when state is blocked but result data exists", () => {
    mockTaskQuery();
    const data: TaskResultQueryData = {
      taskId: "task_available",
      state: "blocked",
      resultStatus: "blocked",
      resultTime: "2026-03-28T10:00:08Z",
      result: buildAvailableResultBody(),
      message: "结果未满足正式展示条件",
    };
    mockedUseTaskResultQuery.mockReturnValue(buildSuccessQueryResult(data) as TaskResultQueryResult);

    const html = renderPage();

    expect(html).toContain("结果已被阻断");
    expect(html).not.toContain("72 分");
    expect(html).not.toContain("开篇抓力");
    expect(html).not.toContain("建议继续观察并进入样章复核。");
  });

  it("does not show result-read failure while task is still active", () => {
    mockedUseTaskQuery.mockReturnValue(
      buildSuccessQueryResult({
        ...buildTaskQueryData(),
        status: "processing",
        resultStatus: "not_available",
        resultAvailable: false,
      }) as TaskQueryResult
    );
    const notReadyError = new Error("not ready");
    mockedUseTaskResultQuery.mockReturnValue({
      data: undefined,
      dataUpdatedAt: 0,
      error: notReadyError,
      errorUpdatedAt: 0,
      failureCount: 1,
      failureReason: notReadyError,
      errorUpdateCount: 1,
      isError: true,
      isFetched: true,
      isFetchedAfterMount: true,
      isFetching: false,
      isLoading: false,
      isPending: false,
      isLoadingError: true,
      isInitialLoading: false,
      isPaused: false,
      isPlaceholderData: false,
      isRefetchError: false,
      isRefetching: false,
      isStale: false,
      isSuccess: false,
      isEnabled: true,
      refetch: vi.fn(),
      status: "error",
      fetchStatus: "idle",
      promise: Promise.resolve(undefined as never),
      isIdle: false,
    } as TaskResultQueryResult);

    const html = renderPage();

    expect(html).toContain("任务尚未进入可读结果状态");
    expect(html).not.toContain("结果读取失败");
  });
});
