import { expect, test, type Page } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const chapterFixture = path.join(currentDir, "fixtures", "chapter.txt");
const outlineFixture = path.join(currentDir, "fixtures", "outline.md");
const successChapters = "第一章里，青岚宗护山大阵突然熄灭，外门弟子顾辞在山门值守时亲眼看见长老重伤归来。执法堂宣布七天后宗门大比照常举行，若无人夺得秘境名额，宗门将被邻宗吞并。顾辞为了保住师父留下的药园，只能冒险借用残缺功法突破境界，同时调查阵法失效的真相。短短一夜里，他先后失去住处、同伴和退路，被迫主动卷入更大的权力斗争。";
const successOutline = "后续主线围绕宗门大比、秘境夺宝和宗门重建展开。顾辞会先在大比中证明自己，再进入秘境寻找修复大阵的核心灵物，同时逐步揭开长老叛变与外敌联手的内幕。中期通过师徒关系、同门竞争和资源争夺持续升级冲突，后期把宗门存亡、个人成长和秘宝兑现收束到同一条升级主线上。";
const blockedChapters = "凌晨四点，婚礼酒店的消防警报骤然响起，许棠穿着还没来得及换下的礼服被困在消防通道。她在未婚夫程屿遗落的公文包里翻出一份股权转让协议，确认父亲留下的广告公司正被一步步架空。程屿带着保安追到后厨时，她抱着原件从员工通道冲进暴雨，赶回公司准备当天不能取消的新品发布会。会议室里，供应商撤单、董事会逼宫和媒体偷拍视频同时压来，她只能临时说服男主所在的竞品团队一起直播反击，把婚约阴谋和公司夺权拉进同一场公开战。到收盘前，她还必须保住核心客户和父亲留下的投票权，否则第二天公司就会被强行并购。";
const blockedOutline = "后续大纲却完全改写为星际机甲远征。主角不再处理婚约、公司和股权争夺，而是带领移民舰队离开母星，在虫族前线争夺失落跃迁引擎。中期主线围绕舰队补给、机甲升级、边境会战和星际政治联盟推进，所有关键矛盾都转向太空战争与军事晋升，和前文都市豪门、职场发布会与股权保卫战没有延续关系。后期再以宇宙级战争收束世界观，与开篇现实都市叙事完全脱节。";

async function waitForCompletedTask(page: Page) {
  await expect(page.getByText("已完成", { exact: true })).toBeVisible({ timeout: 180_000 });

  const completionSignal = page
    .getByRole("link", { name: "查看结果详情" })
    .or(page.getByRole("heading", { name: "任务已结束，但结果被业务阻断" }))
    .first();

  await expect(completionSignal).toBeVisible({ timeout: 180_000 });
}

test("首页关键入口按钮可导航", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "最近任务" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "小说智能打分系统" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /结构化评价结果/ })).toBeVisible();
  await expect(page.getByRole("main").getByRole("link", { name: "新建评测任务" })).toHaveAttribute("href", "/tasks/new");
  await expect(page.getByRole("link", { name: "浏览历史记录" })).toHaveAttribute("href", "/history");
  await expect(page.getByText("API 冻结")).toHaveCount(0);

  await page.goto("/tasks/new");
  await expect(page.getByRole("textbox", { name: "任务标题" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "提交正文与大纲，发起小说结构化评测。" })).toBeVisible();
  await expect(page.getByText("LLM rubric")).toBeVisible();
  await expect(page.getByText("DTO")).toHaveCount(0);

  await page.goto("/history");
  await expect(page.getByRole("textbox", { name: "标题检索" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "按任务回访历史评测记录与结果状态。" })).toBeVisible();
});

test("直接输入成功流可到达结果页", async ({ page }) => {
  await page.goto("/tasks/new");
  await expect(page.getByRole("button", { name: "创建评测任务" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "任务标题" })).toBeVisible();
  await page.getByRole("textbox", { name: "任务标题" }).fill("Playwright 成功流");
  await page.getByRole("textbox", { name: "正文输入" }).fill(successChapters);
  await page.getByRole("textbox", { name: "大纲输入" }).fill(successOutline);

  await expect(page.getByText("正文 + 大纲")).toBeVisible();
  await expect(page.getByText("完整评测")).toBeVisible();

  await page.getByRole("button", { name: "创建评测任务" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_/);
  await waitForCompletedTask(page);
  await expect(page.getByText("结果可用", { exact: true })).toBeVisible();
  await expect(page.getByText("fetch_failed")).toHaveCount(0);

  await page.getByRole("link", { name: "查看结果详情" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_.*\/result/);
  await expect(page.getByRole("heading", { name: "编辑结论与市场判断" })).toBeVisible();
  await expect(page.getByText("结构化评价结果", { exact: true })).toBeVisible();
  await expect(page.getByText("签约概率", { exact: true })).toBeVisible();
  await expect(page.getByText("平台建议", { exact: true })).toBeVisible();
  await expect(page.getByText("Detailed Analysis")).toHaveCount(0);
});

test("跨输入冲突会进入阻断态且结果页不展示正式结果正文", async ({ page }) => {
  await page.goto("/tasks/new");
  await expect(page.getByRole("button", { name: "创建评测任务" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "任务标题" })).toBeVisible();

  await page.getByRole("textbox", { name: "任务标题" }).fill("Playwright 阻断流");
  await page.getByRole("textbox", { name: "正文输入" }).fill(blockedChapters);
  await page.getByRole("textbox", { name: "大纲输入" }).fill(blockedOutline);
  await page.getByRole("button", { name: "创建评测任务" }).click();

  await expect(page).toHaveURL(/\/tasks\/task_/);
  await waitForCompletedTask(page);
  await expect(page.getByText("结果被阻断", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "任务已结束，但结果被业务阻断" })).toBeVisible();

  const taskUrl = page.url();
  await page.goto(`${taskUrl}/result`);
  await expect(page.getByRole("heading", { name: "结果已被阻断" })).toBeVisible();
  await expect(page.getByText(/当前结果被阻断|材料拼接|题材完全不一致/)).toBeVisible();
});

test("文件上传流能创建任务并保留真实输入语义", async ({ page }) => {
  await page.goto("/tasks/new");
  await expect(page.getByRole("button", { name: "创建评测任务" })).toBeVisible();
  await expect(page).toHaveURL(/\/tasks\/new$/);

  await page.getByRole("button", { name: "文件上传" }).click();
  await page.getByRole("textbox", { name: "任务标题" }).fill("Playwright 上传流");
  await page.locator('input[type="file"]').nth(0).setInputFiles(chapterFixture);
  await page.locator('input[type="file"]').nth(1).setInputFiles(outlineFixture);

  await expect(page.getByText("正文 + 大纲")).toBeVisible();
  await expect(page.getByText("文件上传提交")).toBeVisible();

  await page.getByRole("button", { name: "创建评测任务" }).click();
  await expect(page).toHaveURL(/\/tasks\/task_/);
  await waitForCompletedTask(page);
  await expect(page.getByText("结果可用", { exact: true })).toBeVisible();
  await expect(page.getByText("正文 + 大纲")).toBeVisible();
});
