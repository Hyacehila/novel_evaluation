import { describe, expect, it } from "vitest";

import { describeTaskFailure, formatScore, getAxisLabel, getScoreBandLabel, getScoreBandTone } from "@/shared/lib/format";


describe("format helpers", () => {
  it("formats score values with fallback", () => {
    expect(formatScore(75)).toBe("75 分");
    expect(formatScore(0)).toBe("0 分");
    expect(formatScore(null)).toBe("未生成");
  });

  it("maps axis ids to Chinese labels with fallback", () => {
    expect(getAxisLabel("hookRetention")).toBe("开篇抓力");
    expect(getAxisLabel("characterDrive")).toBe("角色驱动");
    expect(getAxisLabel("commercialPotential")).toBe("商业潜力");
    expect(getAxisLabel("unknownAxis")).toBe("unknownAxis");
  });

  it("maps score bands to readable labels with fallback", () => {
    expect(getScoreBandLabel("0")).toBe("不可评或严重失败");
    expect(getScoreBandLabel("3")).toBe("合格");
    expect(getScoreBandLabel("4")).toBe("明显突出");
    expect(getScoreBandLabel("9")).toBe("9");
  });

  it("maps score bands to semantic tones", () => {
    expect(getScoreBandTone("0")).toBe("bad");
    expect(getScoreBandTone("1")).toBe("bad");
    expect(getScoreBandTone("2")).toBe("warn");
    expect(getScoreBandTone("3")).toBe("neutral");
    expect(getScoreBandTone("4")).toBe("good");
  });

  it("returns actionable real provider failure copy", () => {
    expect(describeTaskFailure("TIMEOUT", null)).toContain("真实模型响应超时");
    expect(describeTaskFailure("STAGE_SCHEMA_INVALID", null)).toContain("schema 校验");
    expect(describeTaskFailure("PROVIDER_FAILURE", "模型服务调用失败")).toBe("模型服务调用失败");
  });
});
