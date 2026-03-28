import { expect, test, type Page } from "@playwright/test";

import { providerMode, resetRuntimeProviderKey, submitRuntimeProviderKey } from "./provider-helpers";
const taskCompletionTimeoutMs = 420_000;
const taskFlowTimeoutMs = 720_000;
const successChapters = "第一章里，青岚宗护山大阵突然熄灭，外门弟子顾辞在山门值守时亲眼看见长老重伤归来。执法堂宣布七天后宗门大比照常举行，若无人夺得秘境名额，宗门将被邻宗吞并。顾辞为了保住师父留下的药园，只能冒险借用残缺功法突破境界，同时调查阵法失效的真相。短短一夜里，他先后失去住处、同伴和退路，被迫主动卷入更大的权力斗争。";
const successOutline = "后续主线围绕宗门大比、秘境夺宝和宗门重建展开。顾辞会先在大比中证明自己，再进入秘境寻找修复大阵的核心灵物，同时逐步揭开长老叛变与外敌联手的内幕。中期通过师徒关系、同门竞争和资源争夺持续升级冲突，后期把宗门存亡、个人成长和秘宝兑现收束到同一条升级主线上。";

test.describe.configure({ mode: "serial" });

async function waitForTaskResult(page: Page) {
  const terminalStatus = page
    .getByText("已完成", { exact: true })
    .or(page.getByText("任务失败", { exact: true }))
    .first();

  await expect(terminalStatus).toBeVisible({ timeout: taskCompletionTimeoutMs });

  if (await page.getByText("任务失败", { exact: true }).isVisible()) {
    const failureMessage = await page.locator("main").textContent();
    throw new Error(`任务执行失败：${failureMessage?.trim() ?? "未读取到失败详情"}`);
  }

  await expect(page.getByRole("link", { name: "查看结果详情" })).toBeVisible({ timeout: 60_000 });
}

test("provider 状态场景可按模式完成主流程", async ({ page, request }) => {
  test.setTimeout(taskFlowTimeoutMs);
  await resetRuntimeProviderKey(request);
  await page.goto("/tasks/new");

  await expect(page.getByText("Provider 状态", { exact: true })).toBeVisible();

  if (providerMode === "runtime_key") {
    await expect(page.getByText("当前无 API，无法进行分析").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "创建评测任务" })).toBeDisabled();
    await expect(page.getByLabel("运行时 API Key")).toBeVisible();
    await submitRuntimeProviderKey(page);
    await expect(page.getByText("运行时内存", { exact: true })).toBeVisible();
    await expect(page.getByLabel("运行时 API Key")).toHaveCount(0);
  } else {
    await expect(page.getByText("已配置，可进行分析", { exact: true })).toBeVisible();
    await expect(page.getByText("启动环境变量", { exact: true })).toBeVisible();
    await expect(page.getByLabel("运行时 API Key")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "创建评测任务" })).toBeEnabled();
  }

  await page.getByRole("textbox", { name: "任务标题" }).fill(`Provider ${providerMode} 成功流`);
  await page.getByRole("textbox", { name: "正文输入" }).fill(successChapters);
  await page.getByRole("textbox", { name: "大纲输入" }).fill(successOutline);
  await page.getByRole("button", { name: "创建评测任务" }).click();

  await expect(page).toHaveURL(/\/tasks\/task_/);
  await waitForTaskResult(page);
  await page.getByRole("link", { name: "查看结果详情" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_.*\/result/);
  await expect(page.getByRole("heading", { name: "总体结论与市场判断" })).toBeVisible();
});
