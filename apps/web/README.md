# `apps/web`

该目录用于承载用户交互层。

## 职责

- 接收用户输入的小说文本或文件
- 展示评分结果、分析结果与可视化内容
- 触发评分请求或任务查询
- 消费后端已经校验过的结构化结果

## 不负责

- 不持有正式 Prompt
- 不定义裁判逻辑
- 不直接适配模型供应商
- 不绕过后端自行拼接正式评分请求

## 开工前建议阅读

- `docs/architecture/frontend-overview.md`
- `docs/planning/frontend-page-specs.md`
- `docs/architecture/frontend-technical-route.md`
- `docs/architecture/frontend-app-shell-and-module-boundaries.md`
- `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`

## 后续建议

- 先围绕输入页、任务状态页、结果页与历史记录页搭建页面壳
- 所有结果展示字段以 `packages/schemas/` 中的正式契约为准
- 在后端未完整设计前，优先按 `Mock-First + Adapter-First` 方式推进
