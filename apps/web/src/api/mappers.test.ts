import { describe, expect, it } from "vitest";

import { mapHistoryList, mapProviderStatus, mapResultDetail } from "@/api/mappers";


describe("api mappers", () => {
  it("maps blocked result resource without synthesizing a fake result", () => {
    const view = mapResultDetail({
      taskId: "task_blocked",
      resultStatus: "blocked",
      resultTime: null,
      result: null,
      message: "结果未满足正式展示条件",
    });

    expect(view.state).toBe("blocked");
    expect(view.result).toBeNull();
    expect(view.message).toContain("正式展示条件");
  });

  it("maps history metadata with default limit fallback", () => {
    const view = mapHistoryList({
      items: [],
      meta: {
        nextCursor: null,
      },
    });

    expect(view.meta.limit).toBe(20);
    expect(view.meta.nextCursor).toBeNull();
  });

  it("maps missing provider status with blocking message", () => {
    const view = mapProviderStatus({
      providerId: "provider-deepseek",
      modelId: "deepseek-chat",
      configured: false,
      configurationSource: "missing",
      canAnalyze: false,
      canConfigureFromUi: true,
    });

    expect(view.sourceLabel).toBe("未配置");
    expect(view.statusLabel).toBe("当前无 API，无法进行分析");
    expect(view.blockingMessage).toContain("仍可查看已有任务与结果");
  });
});
