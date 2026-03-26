import { describe, expect, it } from "vitest";

import { mapHistoryList, mapResultDetail } from "@/api/mappers";


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
});
