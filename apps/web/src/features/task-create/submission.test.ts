import { describe, expect, it } from "vitest";

import {
  buildCreateTaskRequest,
  countTrimmedCharacters,
  deriveDraftSemantics,
  formatUploadSize,
  SubmissionValidationError,
} from "@/features/task-create/submission";


describe("task submission builder", () => {
  it("builds a long-opening direct-input payload for chapters and outline", () => {
    const request = buildCreateTaskRequest({
      values: {
        mode: "direct_input",
        analysisMode: "long_opening_outline",
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
      expect(request.payload.analysisMode).toBe("long_opening_outline");
      expect(request.payload.chapters?.[0]?.content).toBe("第一章正文");
      expect(request.payload.outline?.content).toBe("主线大纲");
    }
  });

  it("builds a fulltext direct-input payload without outline", () => {
    const request = buildCreateTaskRequest({
      values: {
        mode: "direct_input",
        analysisMode: "completed_fulltext",
        title: "完结全文",
        chaptersText: "完整正文",
        outlineText: "",
      },
      chaptersFile: null,
      outlineFile: null,
    });

    expect(request.kind).toBe("json");
    if (request.kind === "json") {
      expect(request.payload.analysisMode).toBe("completed_fulltext");
      expect(request.payload.outline).toBeUndefined();
      expect(request.payload.chapters?.[0]?.content).toBe("完整正文");
    }
  });

  it("rejects outline content in fulltext mode", () => {
    expect(() =>
      buildCreateTaskRequest({
        values: {
          mode: "direct_input",
          analysisMode: "completed_fulltext",
          title: "完结全文",
          chaptersText: "完整正文",
          outlineText: "不应提交的大纲",
        },
        chaptersFile: null,
        outlineFile: null,
      })
    ).toThrow(SubmissionValidationError);
  });

  it("rejects unsupported upload extensions", () => {
    expect(() =>
      buildCreateTaskRequest({
        values: {
          mode: "file_upload",
          analysisMode: "long_opening_outline",
          title: "非法文件",
          chaptersText: "",
          outlineText: "",
        },
        chaptersFile: new File(["pdf"], "chapter.pdf", { type: "application/pdf" }),
        outlineFile: new File(["outline"], "outline.txt", { type: "text/plain" }),
      })
    ).toThrow(SubmissionValidationError);
  });

  it("includes analysis mode in multipart requests", () => {
    const request = buildCreateTaskRequest({
      values: {
        mode: "file_upload",
        analysisMode: "completed_fulltext",
        title: "上传全文",
        chaptersText: "",
        outlineText: "",
      },
      chaptersFile: new File(["chapter"], "chapter.txt", { type: "text/plain" }),
      outlineFile: null,
    });

    expect(request.kind).toBe("multipart");
    if (request.kind === "multipart") {
      expect(request.formData.get("analysisMode")).toBe("completed_fulltext");
      expect(request.formData.get("sourceType")).toBe("file_upload");
    }
  });

  it("ignores outline-only drafts in fulltext mode", () => {
    const semantics = deriveDraftSemantics({
      mode: "direct_input",
      analysisMode: "completed_fulltext",
      chaptersText: "",
      outlineText: "只有大纲",
      chaptersFile: null,
      outlineFile: null,
    });

    expect(semantics.inputComposition).toBeNull();
    expect(semantics.isReady).toBe(false);
  });

  it("formats checker text metrics consistently", () => {
    expect(countTrimmedCharacters("  正文内容  ")).toBe(4);
    expect(formatUploadSize(128)).toBe("1 KiB");
    expect(formatUploadSize(1536)).toBe("2 KiB");
    expect(formatUploadSize(1.25 * 1024 * 1024)).toBe("1.3 MiB");
  });
});
