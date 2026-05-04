import { expect, test } from "@playwright/test";

import {
  e2eApiOrigin,
  providerMode,
  realProviderScope,
  resetRuntimeProviderKey,
  submitRuntimeProviderKey,
} from "./provider-helpers";

test.describe.configure({ mode: "serial" });

test("真实 provider auth smoke 可验证启动期或运行时 key", async ({ page, request }) => {
  test.skip(
    realProviderScope !== "auth_smoke" || !["startup_key", "runtime_key"].includes(providerMode),
    "真实 provider auth smoke 需要显式设置 NOVEL_EVAL_E2E_REAL_SCOPE=auth_smoke。",
  );
  test.setTimeout(120_000);

  await resetRuntimeProviderKey(request);
  await page.goto("/tasks/new");
  await expect(page.getByText("Provider 状态", { exact: true })).toBeVisible();

  if (providerMode === "runtime_key") {
    await expect(page.getByText("当前无 API，无法进行分析").first()).toBeVisible();
    await submitRuntimeProviderKey(page);
    await expect(page.getByText("运行时内存", { exact: true })).toBeVisible();
  } else {
    await expect(page.getByText("已配置，可进行分析", { exact: true })).toBeVisible();
    await expect(page.getByText("启动环境变量", { exact: true })).toBeVisible();
  }

  const response = await request.post(`${e2eApiOrigin}/api/provider-status/smoke-test`);
  const envelope = await response.json();

  expect(response.ok(), JSON.stringify(envelope)).toBeTruthy();
  expect(envelope.data).toMatchObject({
    providerId: "provider-deepseek",
    modelId: expect.stringMatching(/^deepseek-v4-/),
    configurationSource: providerMode === "runtime_key" ? "runtime_memory" : "startup_env",
    ok: true,
  });
  expect(envelope.data.durationMs).toBeGreaterThanOrEqual(0);
});
