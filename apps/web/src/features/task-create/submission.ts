import { z } from "zod";

import type { AnalysisMode, CreateTaskJsonPayload, InputComposition } from "@/api/contracts";


const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const allowedExtensions = new Set(["txt", "md", "docx"]);

export const taskCreateFormSchema = z.object({
  mode: z.enum(["direct_input", "file_upload"]),
  analysisMode: z.enum(["long_opening_outline", "completed_fulltext"]),
  title: z.string().trim().min(1, "请输入任务标题"),
  chaptersText: z.string(),
  outlineText: z.string(),
});

export type TaskCreateFormValues = z.infer<typeof taskCreateFormSchema>;

export type CreateTaskSubmissionRequest =
  | {
      kind: "json";
      payload: CreateTaskJsonPayload;
    }
  | {
      kind: "multipart";
      formData: FormData;
    };

export class SubmissionValidationError extends Error {
  readonly field: "title" | "chaptersText" | "outlineText" | "chaptersFile" | "outlineFile";

  constructor(
    field: "title" | "chaptersText" | "outlineText" | "chaptersFile" | "outlineFile",
    message: string
  ) {
    super(message);
    this.name = "SubmissionValidationError";
    this.field = field;
  }
}

export function deriveDraftSemantics({
  mode,
  analysisMode,
  chaptersText,
  outlineText,
  chaptersFile,
  outlineFile,
}: {
  mode: TaskCreateFormValues["mode"];
  analysisMode: AnalysisMode;
  chaptersText: string;
  outlineText: string;
  chaptersFile: File | null;
  outlineFile: File | null;
}): {
  inputComposition: InputComposition | null;
  isReady: boolean;
} {
  const hasChapters = mode === "direct_input" ? chaptersText.trim().length > 0 : Boolean(chaptersFile);
  const hasOutline = analysisMode === "completed_fulltext"
    ? false
    : mode === "direct_input"
      ? outlineText.trim().length > 0
      : Boolean(outlineFile);

  if (analysisMode === "completed_fulltext") {
    return {
      inputComposition: hasChapters ? "chapters_only" : null,
      isReady: hasChapters,
    };
  }

  if (hasChapters && hasOutline) {
    return {
      inputComposition: "chapters_outline",
      isReady: true,
    };
  }
  if (hasChapters) {
    return {
      inputComposition: "chapters_only",
      isReady: false,
    };
  }
  if (hasOutline) {
    return {
      inputComposition: "outline_only",
      isReady: false,
    };
  }

  return {
    inputComposition: null,
    isReady: false,
  };
}

export function buildCreateTaskRequest({
  values,
  chaptersFile,
  outlineFile,
}: {
  values: TaskCreateFormValues;
  chaptersFile: File | null;
  outlineFile: File | null;
}): CreateTaskSubmissionRequest {
  if (values.mode === "direct_input") {
    return buildDirectInputRequest(values);
  }
  return buildMultipartRequest(values, chaptersFile, outlineFile);
}

export function countTrimmedCharacters(value: string) {
  return value.trim().length;
}

export function formatUploadSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.ceil(bytes / 1024))} KiB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MiB`;
}

function buildDirectInputRequest(values: TaskCreateFormValues): CreateTaskSubmissionRequest {
  const chaptersText = values.chaptersText.trim();
  const outlineText = values.outlineText.trim();

  if (values.analysisMode === "long_opening_outline") {
    if (!chaptersText) {
      throw new SubmissionValidationError("chaptersText", "长篇模式需要正文和大纲");
    }
    if (!outlineText) {
      throw new SubmissionValidationError("outlineText", "长篇模式需要正文和大纲");
    }
  } else {
    if (!chaptersText) {
      throw new SubmissionValidationError("chaptersText", "全文模式需要正文");
    }
    if (outlineText) {
      throw new SubmissionValidationError("outlineText", "全文模式不接受大纲");
    }
  }

  return {
    kind: "json",
    payload: {
      title: values.title.trim(),
      analysisMode: values.analysisMode,
      sourceType: "direct_input",
      chapters: chaptersText
        ? [
            {
              title: `${values.title.trim()} 正文`,
              content: chaptersText,
            },
          ]
        : undefined,
      outline: values.analysisMode === "long_opening_outline" && outlineText
        ? {
            content: outlineText,
          }
        : undefined,
    },
  };
}

function buildMultipartRequest(
  values: TaskCreateFormValues,
  chaptersFile: File | null,
  outlineFile: File | null
): CreateTaskSubmissionRequest {
  if (values.analysisMode === "long_opening_outline") {
    if (!chaptersFile || !outlineFile) {
      throw new SubmissionValidationError(
        !chaptersFile ? "chaptersFile" : "outlineFile",
        "长篇模式需要正文文件和大纲文件"
      );
    }
  } else {
    if (!chaptersFile) {
      throw new SubmissionValidationError("chaptersFile", "全文模式需要正文文件");
    }
    if (outlineFile) {
      throw new SubmissionValidationError("outlineFile", "全文模式不接受大纲文件");
    }
  }

  if (chaptersFile) {
    validateUploadFile(chaptersFile, "chaptersFile");
  }
  if (outlineFile) {
    validateUploadFile(outlineFile, "outlineFile");
  }

  const formData = new FormData();
  formData.set("title", values.title.trim());
  formData.set("sourceType", "file_upload");
  formData.set("analysisMode", values.analysisMode);
  if (chaptersFile) {
    formData.set("chaptersFile", chaptersFile);
  }
  if (outlineFile) {
    formData.set("outlineFile", outlineFile);
  }

  return {
    kind: "multipart",
    formData,
  };
}

function validateUploadFile(
  file: File,
  field: "chaptersFile" | "outlineFile"
) {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!allowedExtensions.has(extension)) {
    throw new SubmissionValidationError(field, "仅支持 TXT、MD 或 DOCX 文件");
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new SubmissionValidationError(field, "单个文件大小不能超过 10 MiB");
  }
}
