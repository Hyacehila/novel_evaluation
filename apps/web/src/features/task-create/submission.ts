import { z } from "zod";

import type { CreateTaskJsonPayload, EvaluationMode, InputComposition } from "@/api/contracts";


const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const allowedExtensions = new Set(["txt", "md", "docx"]);

export const taskCreateFormSchema = z.object({
  mode: z.enum(["direct_input", "file_upload"]),
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
  chaptersText,
  outlineText,
  chaptersFile,
  outlineFile,
}: {
  mode: TaskCreateFormValues["mode"];
  chaptersText: string;
  outlineText: string;
  chaptersFile: File | null;
  outlineFile: File | null;
}): {
  inputComposition: InputComposition | null;
  evaluationMode: EvaluationMode | null;
} {
  const hasChapters = mode === "direct_input" ? chaptersText.trim().length > 0 : Boolean(chaptersFile);
  const hasOutline = mode === "direct_input" ? outlineText.trim().length > 0 : Boolean(outlineFile);

  if (hasChapters && hasOutline) {
    return {
      inputComposition: "chapters_outline",
      evaluationMode: "full",
    };
  }
  if (hasChapters) {
    return {
      inputComposition: "chapters_only",
      evaluationMode: "degraded",
    };
  }
  if (hasOutline) {
    return {
      inputComposition: "outline_only",
      evaluationMode: "degraded",
    };
  }
  return {
    inputComposition: null,
    evaluationMode: null,
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

function buildDirectInputRequest(values: TaskCreateFormValues): CreateTaskSubmissionRequest {
  const chaptersText = values.chaptersText.trim();
  const outlineText = values.outlineText.trim();

  if (!chaptersText && !outlineText) {
    throw new SubmissionValidationError("chaptersText", "正文或大纲至少填写一侧");
  }

  return {
    kind: "json",
    payload: {
      title: values.title.trim(),
      sourceType: "direct_input",
      chapters: chaptersText
        ? [
            {
              title: `${values.title.trim()} 正文`,
              content: chaptersText,
            },
          ]
        : undefined,
      outline: outlineText
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
  if (!chaptersFile && !outlineFile) {
    throw new SubmissionValidationError("chaptersFile", "至少上传正文文件或大纲文件中的一项");
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
