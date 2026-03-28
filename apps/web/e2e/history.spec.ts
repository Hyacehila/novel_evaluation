import { expect, test, type APIRequestContext } from "@playwright/test";

import { ensureProviderReady, resetRuntimeProviderKey } from "./provider-helpers";

async function createTask(
  request: APIRequestContext,
  payload: {
    title: string;
    chapters: string;
    outline?: string;
  }
) {
  const response = await request.post("/api/tasks", {
    data: {
      title: payload.title,
      chapters: [{ title: `${payload.title} 正文`, content: payload.chapters }],
      outline: payload.outline ? { content: payload.outline } : undefined,
      sourceType: "direct_input",
    },
  });
  expect(response.ok()).toBeTruthy();
  const envelope = await response.json();
  const taskId = envelope.data.taskId as string;

  await expect
    .poll(async () => {
      const taskResponse = await request.get(`/api/tasks/${taskId}`);
      const taskEnvelope = await taskResponse.json();
      return taskEnvelope.data.status as string;
    }, { timeout: 120_000 })
    .toBe("completed");
}

test("历史页支持标题、状态与分页回访", async ({ page, request }) => {
  await resetRuntimeProviderKey(request);
  await ensureProviderReady(page);
  await createTask(request, {
    title: "星际远征一号",
    chapters: "剧情梗概：舰长林澈将率舰队离开母星，途中发现补给名单被人篡改，随后会在边境战场里调查幕后黑手并夺回航道控制权。当前只给出事件摘要，没有展开成具体场景、对白和连续叙事。",
    outline: "大纲摘要：前期出发，中期调查背叛，后期夺回要塞并重建联盟。",
  });
  await createTask(request, {
    title: "都市日常一号",
    chapters: "剧情梗概：编辑周宁会接手停更专栏、处理同事竞争、完成栏目重建，并在家庭催婚与职业成长之间做选择。当前材料只有提纲式摘要，没有真正展开正文事件。",
    outline: "大纲摘要：前期接手栏目，中期团队磨合，后期职业选择与关系收束。",
  });
  await createTask(request, {
    title: "星际余烬二号",
    chapters: "剧情梗概：顾霄会在战后废墟里接手难民舰艇、重建舰队秩序、清算旧上级并夺回补给线。这里仍然只是大纲压缩版，没有连续动作场景和可验证的叙事细节。",
    outline: "大纲摘要：前期整编舰队，中期追查阴谋，后期夺回要塞与补给线。",
  });

  await page.goto("/history?limit=1");

  const queryInput = page.getByRole("textbox", { name: "标题检索" });
  await expect(queryInput).toBeVisible();
  await expect(page.getByRole("heading", { name: "任务回访", exact: true })).toBeVisible();
  await expect(page.getByText("历史评测记录", { exact: true })).toBeVisible();
  await expect(page.getByText("每页 1 条")).toBeVisible();
  await expect(page.getByRole("button", { name: "下一页" })).toBeVisible();
  await expect(page.getByText("q / status / cursor / limit")).toHaveCount(0);
  await queryInput.fill("星际");
  await expect.poll(() => page.url(), { timeout: 10_000 }).toMatch(/q=%E6%98%9F%E9%99%85/);
  await expect(queryInput).toHaveValue("星际");

  await page.getByRole("combobox", { name: "任务状态" }).selectOption("completed");
  await expect.poll(() => page.url()).toMatch(/status=completed/);
  await expect(page.locator("article").getByText("任务失败", { exact: true })).toHaveCount(0);

  await expect(page.getByRole("button", { name: "下一页" })).toBeVisible();
  await page.getByRole("button", { name: "清空筛选" }).click();
  await expect.poll(() => page.url()).toMatch(/\/history$/);
  await expect(queryInput).toHaveValue("");
  await expect(page.getByText("DTO")).toHaveCount(0);
});
