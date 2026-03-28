import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  configureRuntimeProviderKey,
  describeApiError,
  fetchProviderStatus,
} from "@/api/client";


const originalFetch = global.fetch;

afterEach(() => {
  vi.restoreAllMocks();
  global.fetch = originalFetch;
});

function mockFetchJson(payload: unknown, status = 200) {
  const fetchMock = vi.fn(async () => {
    return new Response(JSON.stringify(payload), {
      status,
      headers: {
        "content-type": "application/json",
      },
    });
  });
  global.fetch = fetchMock as typeof fetch;
  return fetchMock;
}

describe("provider status client", () => {
  it("maps missing provider status into a blocked view", async () => {
    mockFetchJson({
      success: true,
      data: {
        providerId: "provider-deepseek",
        modelId: "deepseek-chat",
        configured: false,
        configurationSource: "missing",
        canAnalyze: false,
        canConfigureFromUi: true,
      },
    });

    const view = await fetchProviderStatus();

    expect(view.configurationSource).toBe("missing");
    expect(view.canAnalyze).toBe(false);
    expect(view.canConfigureFromUi).toBe(true);
    expect(view.sourceLabel).toBe("未配置");
    expect(view.blockingMessage).toContain("当前无 API，无法进行分析");
  });

  it("maps startup env provider status into an analyzable view", async () => {
    mockFetchJson({
      success: true,
      data: {
        providerId: "provider-deepseek",
        modelId: "deepseek-chat",
        configured: true,
        configurationSource: "startup_env",
        canAnalyze: true,
        canConfigureFromUi: false,
      },
    });

    const view = await fetchProviderStatus();

    expect(view.configurationSource).toBe("startup_env");
    expect(view.canAnalyze).toBe(true);
    expect(view.canConfigureFromUi).toBe(false);
    expect(view.sourceLabel).toBe("启动环境变量");
    expect(view.blockingMessage).toBeNull();
  });

  it("posts runtime key payload to the configuration endpoint", async () => {
    const fetchMock = mockFetchJson({
      success: true,
      data: {
        providerId: "provider-deepseek",
        modelId: "deepseek-chat",
        configured: true,
        configurationSource: "runtime_memory",
        canAnalyze: true,
        canConfigureFromUi: false,
      },
    });

    const view = await configureRuntimeProviderKey({ apiKey: "sk-test" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/provider-status/runtime-key",
      expect.objectContaining({
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({ apiKey: "sk-test" }),
        cache: "no-store",
      })
    );
    expect(view.configurationSource).toBe("runtime_memory");
    expect(view.canAnalyze).toBe(true);
    expect(view.sourceLabel).toBe("运行时内存");
  });

  it("returns friendly provider configuration messages", () => {
    const missingProviderError = new ApiClientError(
      409,
      {
        code: "PROVIDER_NOT_CONFIGURED",
        message: "ignored",
      },
      "fallback"
    );
    const lockedProviderError = new ApiClientError(
      409,
      {
        code: "PROVIDER_CONFIGURATION_LOCKED",
        message: "ignored",
      },
      "fallback"
    );

    expect(describeApiError(missingProviderError)).toContain("当前 provider 未配置");
    expect(describeApiError(lockedProviderError)).toContain("不支持在 UI 中重新录入");
  });
});
