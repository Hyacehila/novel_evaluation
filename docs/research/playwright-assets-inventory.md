# Playwright 研究产物清单

本文档用于记录当前仓库中已知的抓取与分析产物。

## 已知文件

- `output/playwright/page.html`
- `output/playwright/formatted.js`
- `output/playwright/index-BEkHPCRt.js`

## 定位

这些文件统一视为：

- 页面抓取产物
- 静态资源快照
- 分析辅助产物
- 研究输入材料

## 非正式源码原则

- 不将这些文件纳入 `apps/` 或 `packages/`
- 不直接依赖这些文件实现正式业务逻辑
- 如需吸收其中信息，应转写到正式文档中

## 当前价值

- 辅助确认现有产品的接口形态
- 辅助确认前端消费字段
- 辅助确认结果结构和兼容约束
