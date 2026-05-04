import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useConfigureRuntimeProviderKeyMutation, useProviderStatusQuery } from "@/api/hooks";
import { AppShell } from "@/shared/layouts/app-shell";

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
  usePathname: () => "/tasks/new",
}));

vi.mock("@/api/hooks", () => ({
  useConfigureRuntimeProviderKeyMutation: vi.fn(),
  useProviderStatusQuery: vi.fn(),
}));

const mockedUseConfigureRuntimeProviderKeyMutation = vi.mocked(useConfigureRuntimeProviderKeyMutation);
const mockedUseProviderStatusQuery = vi.mocked(useProviderStatusQuery);

describe("app shell", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    mockedUseConfigureRuntimeProviderKeyMutation.mockReturnValue({
      isPending: false,
      mutateAsync: vi.fn(),
    } as unknown as ReturnType<typeof useConfigureRuntimeProviderKeyMutation>);
    mockedUseProviderStatusQuery.mockReturnValue({
      data: {
        providerId: "provider-deepseek",
        modelId: "deepseek-v4-pro",
        configured: true,
        configurationSource: "startup_env",
        canAnalyze: true,
        canConfigureFromUi: false,
        sourceLabel: "启动环境变量",
        statusLabel: "已配置，可进行分析",
        blockingMessage: null,
      },
      isError: false,
      isPending: false,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useProviderStatusQuery>);
  });

  it("renders a skip link and stable main target", () => {
    const html = renderToStaticMarkup(createElement(AppShell, null, createElement("p", null, "页面内容")));

    expect(html).toContain('href="#main-content"');
    expect(html).toContain('id="main-content"');
    expect(html).toContain("Provider 状态");
    expect(html).toContain("页面内容");
  });
});
