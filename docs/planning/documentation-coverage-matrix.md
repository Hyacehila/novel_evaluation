# 文档覆盖矩阵

## 文档目的

本文档维护“主题 -> 主真源”的映射，确保同一规则不被多个文档重复冻结。

## 主题覆盖矩阵

| 主题 | 主真源文档 | 辅助文档 | 备注 |
| --- | --- | --- | --- |
| 系统总体目标与交付定位 | `docs/architecture/system-overview.md` | `README.md` | 系统整体定位 |
| Phase 1 范围与排除项 | `docs/planning/mvp-phase-1-scope.md` | `docs/planning/layered-rubric-implementation-plan.md` | 当前阶段做什么/不做什么 |
| 实施波次与 mission 路线 | `docs/planning/layered-rubric-implementation-plan.md` | `docs/planning/devfleet-mission-catalog.md`、`docs/planning/devfleet-mission-dag.md` | 交付路线 |
| 运行时执行与持久化 | `docs/architecture/runtime-execution-and-persistence.md` | `docs/architecture/system-overview.md`、`docs/operations/local-development-topology.md` | `SQLite`、进程内执行、重启语义 |
| 后端技术路线 | `docs/architecture/backend-technical-route.md` | `docs/decisions/ADR-005-backend-technical-route.md` | 后端技术基线 |
| 应用层职责边界 | `docs/architecture/application-layer-boundaries.md` | `docs/architecture/integration-boundaries.md` | 目录与依赖边界 |
| Provider 运行时 I/O 契约 | `docs/contracts/provider-execution-contract.md` | `docs/architecture/provider-abstraction.md` | provider port 真源 |
| 文件上传与摄取边界 | `docs/contracts/file-upload-and-ingestion-boundary.md` | `apps/api/contracts/api-v0-overview.md`、前端输入契约 | 上传字段、格式、大小、错误码 |
| API 资源与接口语义 | `apps/api/contracts/api-v0-overview.md` | `docs/contracts/frontend-minimal-api-assumptions.md` | API v0 |
| 任务状态与错误语义 | `apps/api/contracts/job-lifecycle-and-error-semantics.md` | `docs/architecture/frontend-task-and-state-flow.md` | 状态与错误码主真源 |
| 正式结果结构语义 | `docs/contracts/json-contracts.md` | `packages/schemas/output/` | 对外结果语义 |
| 阶段中间结构语义 | `docs/contracts/rubric-stage-contracts.md` | `packages/schemas/stages/`、`docs/architecture/scoring-pipeline.md` | 中间阶段对象 |
| Canonical schema 对象索引 | `docs/contracts/canonical-schema-index.md` | `packages/schemas/` | 对象级索引 |
| Prompt 生命周期与资产格式 | `docs/prompting/prompt-lifecycle.md` | `prompts/*.md`、`packages/prompt-runtime/README.md` | Markdown/YAML 资产治理 |
| 集成边界 | `docs/architecture/integration-boundaries.md` | `docs/architecture/application-layer-boundaries.md` | 跨模块交互 |
| Evals 框架与统一报告 | `docs/architecture/evals-framework.md` | `evals/*.md`、`packages/schemas/evals/README.md` | `EvalReport` / baseline 口径 |
| 前端技术路线 | `docs/architecture/frontend-technical-route.md` | `docs/contracts/frontend-api-consumption-and-query-strategy.md` | `pnpm`、query/form 基线 |
| 前端输入与提交边界 | `docs/contracts/frontend-input-and-submit-spec.md` | `docs/contracts/frontend-backend-boundary.md` | 上传与提交边界 |
| 前端 API 消费与历史查询策略 | `docs/contracts/frontend-api-consumption-and-query-strategy.md` | `docs/contracts/frontend-minimal-api-assumptions.md` | Query、轮询、history |
| 页面规格 | `docs/planning/frontend-page-specs.md` | `docs/architecture/frontend-overview.md` | 页面职责与状态 |
| 本地运行配置与诊断 | `docs/operations/runtime-configuration-and-diagnostics.md` | `docs/operations/local-development-topology.md` | env 与诊断字段 |
| 本地安装与 smoke | `docs/operations/local-installation-and-smoke.md` | `docs/operations/README.md` | 安装、启动、验证命令 |

## 联动更新矩阵

### 更新 `docs/architecture/runtime-execution-and-persistence.md` 时

至少检查：

- `docs/planning/mvp-phase-1-scope.md`
- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/operations/local-development-topology.md`
- `docs/operations/runtime-configuration-and-diagnostics.md`

### 更新 `docs/contracts/provider-execution-contract.md` 时

至少检查：

- `docs/architecture/provider-abstraction.md`
- `packages/provider-adapters/README.md`
- `docs/operations/runtime-configuration-and-diagnostics.md`
- `docs/architecture/integration-boundaries.md`

### 更新 `docs/contracts/file-upload-and-ingestion-boundary.md` 时

至少检查：

- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/frontend-input-and-submit-spec.md`
- `docs/contracts/frontend-backend-boundary.md`

### 更新 `apps/api/contracts/api-v0-overview.md` 时

至少检查：

- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- `docs/contracts/file-upload-and-ingestion-boundary.md`

### 更新 `docs/prompting/prompt-lifecycle.md` 时

至少检查：

- `prompts/README.md`
- `prompts/registry/README.md`
- `prompts/versions/README.md`
- `prompts/scoring/README.md`
- `packages/prompt-runtime/README.md`

### 更新 `docs/operations/runtime-configuration-and-diagnostics.md` 时

至少检查：

- `docs/operations/local-installation-and-smoke.md`
- `docs/architecture/runtime-execution-and-persistence.md`
- `apps/worker/README.md`
- `README.md`

## 禁止重复定义的主题

- `SQLite` 持久化与重启语义
- provider port 字段集合
- 上传字段、格式、大小和错误码
- 历史查询 `q/status/cursor/limit`
- `EvalReport.reportType`
- `segmentationPlan` 正式字段
- Prompt 资产文件格式

## 完成标准

- 每个主题都有单一主锚点
- 新文档不再复制同一规则
- 变更关键规则时能清楚知道要联动哪些文档
