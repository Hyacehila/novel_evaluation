import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const providerMode = process.env.NOVEL_EVAL_E2E_PROVIDER_MODE ?? "deterministic";
const runtimeApiKey = process.env.NOVEL_EVAL_DEEPSEEK_API_KEY ?? "";
const e2eApiOrigin = process.env.NOVEL_EVAL_E2E_API_ORIGIN ?? "http://127.0.0.1:18000";

export async function resetRuntimeProviderKey(request: APIRequestContext) {
  if (providerMode !== "runtime_key") {
    return;
  }

  const response = await request.delete(`${e2eApiOrigin}/api/provider-status/runtime-key`);
  expect(response.ok()).toBeTruthy();
  const envelope = await response.json();
  expect(envelope.data).toMatchObject({
    configured: false,
    configurationSource: "missing",
    canAnalyze: false,
    canConfigureFromUi: true,
  });
}

export async function submitRuntimeProviderKey(page: Page) {
  expect(runtimeApiKey, "runtime_key 场景需要 NOVEL_EVAL_DEEPSEEK_API_KEY").not.toBe("");
  await expect(page.getByLabel("运行时 API Key")).toBeVisible();
  await page.getByLabel("运行时 API Key").fill(runtimeApiKey);
  await page.getByRole("button", { name: "录入运行时 Key" }).click();
  await expect(page.getByText("已配置，可进行分析", { exact: true })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: "创建评测任务" })).toBeEnabled();
}

export async function ensureProviderReady(page: Page) {
  if (providerMode !== "runtime_key") {
    return;
  }

  await page.goto("/tasks/new");
  await expect(page.getByText("Provider 状态", { exact: true })).toBeVisible();
  if (await page.getByText("已配置，可进行分析", { exact: true }).count()) {
    return;
  }

  await expect(page.getByText("当前无 API，无法进行分析").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "创建评测任务" })).toBeDisabled();
  await submitRuntimeProviderKey(page);
}
