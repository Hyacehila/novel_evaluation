# 面向网络小说联合投稿包全 LLM Rubric 主线的实施计划

## 文档目的

本文档记录当前 `Phase 1` 主线的真实落地状态，并把下一阶段判断锚定到交付收口而不是 implementation-prep。

## 当前判断

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Yes`
- `Runtime-Ready = Yes`
- `End-to-End Alpha = Yes`
- `Delivery-Ready = Partial`

## 当前已落地现实

- `packages/schemas/`：`common / input / output / stages / evals` 全部已落地
- `packages/application/`：正式五段评分主线、阻断语义、失败映射与 SQLite 任务流已落地
- `packages/provider-adapters/`：DeepSeek adapter + 本地 deterministic fallback 已落地
- `packages/prompt-runtime/`：registry / versions / Markdown 正文解析已落地
- `apps/api/`：固定 API v0、上传边界、history 查询、SQLite 持久化、恢复语义已落地
- `apps/worker/`：`eval / batch` 真实 CLI、baseline/report/records 写出已落地
- `evals/`：datasets / suite / runner / builders / writers 已落地
- `apps/web/`：首页、输入页、任务页、结果页、历史页已落地

## 当前剩余交付项

- 在一台全新环境按文档完整走一次安装、启动、smoke 与回滚演练
- 如需正式把阶段上调为 `Delivery-Ready = Yes`，应以该演练记录为准

## 当前执行约束

- 不得新增公开 API 路由
- 不得引入多用户、鉴权、SSE、WebSocket、多 Provider 生产切换
- `worker` 继续只负责回归与批处理
- 前端继续只消费现有 API v0
