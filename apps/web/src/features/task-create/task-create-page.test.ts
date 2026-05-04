import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useCreateTaskMutation, useProviderStatusQuery } from "@/api/hooks";
import { TaskCreatePage } from "@/features/task-create/task-create-page";

vi.mock("next/link", async () => {
  const React = await import("react");

  return {
    default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => {
      void _prefetch;
      return React.createElement("a", { href, ...props }, children);
    },
  };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock("@/api/hooks", () => ({
  useCreateTaskMutation: vi.fn(),
  useProviderStatusQuery: vi.fn(),
}));

const mockedUseCreateTaskMutation = vi.mocked(useCreateTaskMutation);
const mockedUseProviderStatusQuery = vi.mocked(useProviderStatusQuery);

function mockCreateMutation() {
  mockedUseCreateTaskMutation.mockReturnValue({
    isPending: false,
    mutateAsync: vi.fn(),
  } as unknown as ReturnType<typeof useCreateTaskMutation>);
}

function mockProviderStatus(canAnalyze = true) {
  mockedUseProviderStatusQuery.mockReturnValue({
    data: {
      providerId: "provider-deepseek",
      modelId: "deepseek-v4-pro",
      configured: canAnalyze,
      configurationSource: canAnalyze ? "startup_env" : "missing",
      canAnalyze,
      canConfigureFromUi: !canAnalyze,
      sourceLabel: canAnalyze ? "启动环境变量" : "未配置",
      statusLabel: canAnalyze ? "已配置，可进行分析" : "当前无 API，无法进行分析",
      blockingMessage: canAnalyze ? null : "当前无 API，无法进行分析。",
    },
    isError: false,
    isPending: false,
  } as unknown as ReturnType<typeof useProviderStatusQuery>);
}

function renderPage() {
  return renderToStaticMarkup(createElement(TaskCreatePage));
}

describe("task create page", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockCreateMutation();
  });

  it("renders segmented native radio controls and the submit checker", () => {
    mockProviderStatus(true);

    const html = renderPage();

    expect(html).toContain('role="radiogroup"');
    expect(html).toContain('type="radio"');
    expect(html).toContain('name="analysisMode"');
    expect(html).toContain('name="inputMode"');
    expect(html).toContain("提交检查器");
    expect(html).toContain("正文字符数");
    expect(html).toContain("大纲字符数");
    expect(html).toContain("Provider 状态");
    expect(html).toContain("已配置，可进行分析");
  });

  it("shows provider blocking state inside the checker", () => {
    mockProviderStatus(false);

    const html = renderPage();

    expect(html).toContain("当前无 API，无法进行分析");
    expect(html).toContain("Provider 状态");
    expect(html).toContain("阻断");
  });
});
