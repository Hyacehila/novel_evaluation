# 小说智能打分系统仓库

本仓库当前锚定的唯一交付目标是 `Phase 1`：开源、本地部署、单用户、可运行的小说智能打分系统。正式交付边界已经冻结为 `SQLite` 单文件持久化、`API` 进程内异步执行用户任务、`worker` 仅承接回归与批处理、上传格式固定为 `TXT/MD/DOCX`、前端包管理器固定为 `pnpm`。

## Phase 1 冻结结论

- 后端基线：`Python 3.13 + uv + FastAPI + Pydantic`
- 前端基线：`Next.js (App Router) + React + TypeScript + pnpm`
- Provider：`DeepSeek API`
- 评分编排：`PocketFlow`
- 本地状态存储：`SQLite`
- 默认数据库路径：`./var/novel-evaluation.sqlite3`
- 用户任务执行模型：`apps/api` 进程内异步执行
- `worker` 职责：只运行批处理与回归
- 历史查询：正式支持 `q/status/cursor/limit`
- 当前继续排除：鉴权、多租户、`SSE`、`WebSocket`、多 Provider 生产级切换

## 当前现实

- 文档真源已经覆盖范围、架构、契约、运维与实施计划
- 最小后端基线已存在：`packages/schemas/`、`packages/application/`、`apps/api/` 和测试
- 前端、真实评分运行时、正式 Provider adapter、Prompt runtime、worker/evals、持久化实现仍待开发
- 因此当前结论仍是：
  - `Doc-Ready = Yes`
  - `Implementation-Ready = Not Yet`
  - `Delivery-Ready = Not Yet`

## 顶层目录

- `apps/`：可运行应用入口，包含 `api`、`web`、`worker`
- `packages/`：可复用核心模块，包含 application、provider-adapters、prompt-runtime、schemas 等
- `prompts/`：正式 Prompt 资产与版本元数据
- `evals/`：评测样本、用例、runner、baseline、report
- `docs/`：范围、架构、契约、运维、决策与实施计划
- `output/`：研究、抓取与临时产物
- `scripts/`：仓库维护和自动化脚本

## 关键文档

1. `docs/planning/mvp-phase-1-scope.md`
2. `docs/architecture/system-overview.md`
3. `docs/architecture/runtime-execution-and-persistence.md`
4. `apps/api/contracts/api-v0-overview.md`
5. `apps/api/contracts/job-lifecycle-and-error-semantics.md`
6. `docs/contracts/file-upload-and-ingestion-boundary.md`
7. `docs/contracts/provider-execution-contract.md`
8. `docs/contracts/rubric-stage-contracts.md`
9. `docs/operations/runtime-configuration-and-diagnostics.md`
10. `docs/operations/local-installation-and-smoke.md`
