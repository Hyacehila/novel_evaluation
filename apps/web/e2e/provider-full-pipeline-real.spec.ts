import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import {
  e2eApiOrigin,
  providerMode,
  realProviderScope,
  resetRuntimeProviderKey,
  submitRuntimeProviderKey,
} from "./provider-helpers";

const realTaskTimeoutMs = Number(process.env.NOVEL_EVAL_E2E_REAL_TASK_TIMEOUT_MS ?? 1_800_000);
const pollIntervalMs = 5_000;
const realChapters =
  "第一章，旧城区突然停电，修表工林照在废楼里听见失踪妹妹留下的录音。录音说午夜前必须找到三枚旧钥匙，否则整栋楼会被拆除。林照先救下被困的邻居，又发现物业、拆迁队和妹妹的研究笔记都指向同一间地下配电室。";
const realOutline =
  "后续主线围绕三枚钥匙、地下配电室和妹妹失踪真相展开。林照会逐层确认邻居隐瞒的事故、拆迁队伪造的文件和旧楼供电系统里的实验记录，最后在拆楼前救出妹妹，并揭开停电是人为制造的控制实验。";

test.describe.configure({ mode: "serial" });

async function configureProviderForRealRun(page: Page, request: APIRequestContext) {
  await resetRuntimeProviderKey(request);
  await page.goto("/tasks/new");
  await expect(page.getByText("Provider 状态", { exact: true })).toBeVisible();

  if (providerMode === "runtime_key") {
    await submitRuntimeProviderKey(page);
    await expect(page.getByText("运行时内存", { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("启动环境变量", { exact: true })).toBeVisible();
  }
}

async function waitForTaskTerminal(request: APIRequestContext, taskId: string) {
  const startedAt = Date.now();
  let lastTask: Record<string, unknown> | null = null;

  while (Date.now() - startedAt < realTaskTimeoutMs) {
    const response = await request.get(`${e2eApiOrigin}/api/tasks/${taskId}`);
    const envelope = await response.json();
    expect(response.ok(), JSON.stringify(envelope)).toBeTruthy();
    lastTask = envelope.data;
    if (lastTask?.status === "completed" || lastTask?.status === "failed") {
      return lastTask;
    }
    await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
  }

  throw new Error(
    `真实 full-pipeline E2E 等待任务终态超时：taskId=${taskId}, timeoutMs=${realTaskTimeoutMs}, lastTask=${JSON.stringify(lastTask)}`,
  );
}

test("真实 provider full-pipeline 完成结果页或给出明确失败诊断", async ({ page, request }) => {
  test.skip(
    realProviderScope !== "full_pipeline" || !["startup_key", "runtime_key"].includes(providerMode),
    "真实 full-pipeline 需要显式设置 NOVEL_EVAL_E2E_REAL_SCOPE=full_pipeline。",
  );
  test.setTimeout(realTaskTimeoutMs + 180_000);

  await configureProviderForRealRun(page, request);
  await page.getByRole("textbox", { name: "任务标题" }).fill(`Real ${providerMode} full pipeline`);
  await page.getByRole("textbox", { name: "正文输入" }).fill(realChapters);
  await page.getByRole("textbox", { name: "大纲输入" }).fill(realOutline);
  await page.getByRole("button", { name: "创建评测任务" }).click();

  await expect(page).toHaveURL(/\/tasks\/task_/);
  const taskId = page.url().match(/\/tasks\/([^/]+)/)?.[1];
  expect(taskId).toBeTruthy();

  const terminalTask = await waitForTaskTerminal(request, taskId as string);
  await page.goto(`/tasks/${taskId}`);

  if (terminalTask.status === "failed") {
    expect(["TIMEOUT", "STAGE_SCHEMA_INVALID", "PROVIDER_FAILURE"]).toContain(terminalTask.errorCode);
    await expect(page.getByText("任务执行失败", { exact: true })).toBeVisible();
    await expect(
      page
        .getByText("真实模型响应超时")
        .or(page.getByText("schema 校验"))
        .or(page.getByText("API key、额度或上游状态")),
    ).toBeVisible();
    return;
  }

  expect(terminalTask.resultStatus).toBe("available");
  await expect(page.getByRole("link", { name: "查看结果详情" })).toBeVisible({ timeout: 60_000 });
  await page.getByRole("link", { name: "查看结果详情" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_.*\/result/);
  await expect(page.getByRole("heading", { name: "总体结论与市场判断" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "类型判断与 4 个 lens" })).toBeVisible();
});
