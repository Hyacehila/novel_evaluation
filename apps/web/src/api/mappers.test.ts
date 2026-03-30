import { describe, expect, it } from "vitest";

import { mapDashboardSummary, mapHistoryList, mapProviderStatus, mapResultDetail } from "@/api/mappers";


describe("api mappers", () => {
  it("maps available result resource with axes and overall", () => {
    const view = mapResultDetail({
      taskId: "task_available",
      resultStatus: "available",
      resultTime: "2026-03-28T10:00:00Z",
      result: {
        taskId: "task_available",
        schemaVersion: "1.0.0",
        promptVersion: "v2",
        rubricVersion: "rubric-v2",
        providerId: "provider-deepseek",
        modelId: "deepseek-chat",
        resultTime: "2026-03-28T10:00:00Z",
        axes: [
          {
            axisId: "hookRetention",
            scoreBand: "3",
            score: 75,
            summary: "开篇抓力稳定。",
            reason: "冲突出现及时。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "serialMomentum",
            scoreBand: "3",
            score: 75,
            summary: "连载目标明确。",
            reason: "阶段目标清晰。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "characterDrive",
            scoreBand: "3",
            score: 75,
            summary: "角色驱动成立。",
            reason: "动机清楚。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "narrativeControl",
            scoreBand: "3",
            score: 75,
            summary: "叙事控制稳定。",
            reason: "信息组织清晰。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "pacingPayoff",
            scoreBand: "3",
            score: 75,
            summary: "节奏兑现合理。",
            reason: "推进与回收对应。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "settingDifferentiation",
            scoreBand: "3",
            score: 75,
            summary: "设定有辨识度。",
            reason: "题材标签稳定。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "platformFit",
            scoreBand: "3",
            score: 75,
            summary: "平台适配度较稳。",
            reason: "受众预期匹配。",
            degradedByInput: false,
            riskTags: [],
          },
          {
            axisId: "commercialPotential",
            scoreBand: "3",
            score: 75,
            summary: "商业潜力可观察。",
            reason: "具备追读空间。",
            degradedByInput: false,
            riskTags: [],
          },
        ],
        overall: {
          score: 75,
          verdict: "建议继续观察并进入样章复核。",
          verdictSubQuote: "情感密度与节奏控制更贴合深耕慢热读者的平台气质。",
          summary: "整体完成度稳定。",
          platformCandidates: [
            { name: "女频平台 A", weight: 70, pitchQuote: "情感流向与平台核心读者群体高度匹配。" },
            { name: "女频平台 B", weight: 30, pitchQuote: "题材定位次级适配，可作为备选投放渠道。" },
          ],
          marketFit: "当前题材更贴合女频平台 A 的用户预期。",
          strengths: ["情感抓手清晰"],
          weaknesses: ["长线兑现仍需观察"],
        },
      },
      message: null,
    });

    expect(view.state).toBe("available");
    expect(view.result?.axes).toHaveLength(8);
    expect(view.result?.overall.score).toBe(75);
    expect(view.result?.overall.verdict).toContain("继续观察");
    expect("signingProbability" in (view.result ?? {})).toBe(false);
  });

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

  it("maps dashboard summary recent results with overall fields", () => {
    const view = mapDashboardSummary({
      recentTasks: [],
      activeTasks: [],
      recentResults: [
        {
          taskId: "task_available",
          title: "测试稿件",
          resultTime: "2026-03-28T10:00:00Z",
          overallScore: 75,
          overallVerdict: "建议继续观察并进入样章复核。",
        },
      ],
    });

    expect(view.recentResults[0].overallScore).toBe(75);
    expect(view.recentResults[0].overallVerdict).toContain("继续观察");
    expect("signingProbability" in view.recentResults[0]).toBe(false);
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
