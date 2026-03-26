import { describe, expect, it } from "vitest";

import {
  buildCreateTaskRequest,
  deriveDraftSemantics,
  SubmissionValidationError,
} from "@/features/task-create/submission";


describe("task submission builder", () => {
  it("builds a direct-input payload for chapters and outline", () => {
    const request = buildCreateTaskRequest({
      values: {
        mode: "direct_input",
        title: "修仙长篇",
        chaptersText: "第一章正文",
        outlineText: "主线大纲",
      },
      chaptersFile: null,
      outlineFile: null,
    });

    expect(request.kind).toBe("json");
    if (request.kind === "json") {
      expect(request.payload.sourceType).toBe("direct_input");
      expect(request.payload.chapters?.[0]?.content).toBe("第一章正文");
      expect(request.payload.outline?.content).toBe("主线大纲");
    }
  });

  it("rejects unsupported upload extensions", () => {
    expect(() =>
      buildCreateTaskRequest({
        values: {
          mode: "file_upload",
          title: "非法文件",
          chaptersText: "",
          outlineText: "",
        },
        chaptersFile: new File(["pdf"], "chapter.pdf", { type: "application/pdf" }),
        outlineFile: null,
      })
    ).toThrow(SubmissionValidationError);
  });

  it("marks single-side input as degraded", () => {
    const semantics = deriveDraftSemantics({
      mode: "direct_input",
      chaptersText: "",
      outlineText: "只有大纲",
      chaptersFile: null,
      outlineFile: null,
    });

    expect(semantics.inputComposition).toBe("outline_only");
    expect(semantics.evaluationMode).toBe("degraded");
  });
});
