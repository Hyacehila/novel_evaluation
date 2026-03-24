# 文档覆盖矩阵

## 文档目的

本文档用于建立“问题领域 -> 真源文档”的映射关系，减少后续文档扩张时的重复定义、职责混乱和相互冲突。

本文档回答的问题是：

- 某个主题应该看哪份文档
- 某类问题由哪份文档拥有定义权
- 更新某份文档时需要联动检查哪些文档

本文档不负责：

- 替代任何主题真源文档
- 重新解释所有领域内容

## 使用原则

- 每个主题应尽量有单一主锚点文档
- 其它文档引用而不是复制定义
- 若发现一类主题在多个文档中重复定义，应以本矩阵推动收敛

## 主题覆盖矩阵

| 主题 | 主真源文档 | 辅助文档 | 备注 |
| --- | --- | --- | --- |
| 系统总体目标与层级 | `docs/architecture/system-overview.md` | `README.md` | 负责系统整体定位 |
| Phase 1 范围 | `docs/planning/mvp-phase-1-scope.md` | `docs/planning/layered-rubric-implementation-plan.md`、`docs/architecture/backend-technical-route.md` | 负责当前阶段做什么/不做什么 |
| 后端技术路线 | `docs/architecture/backend-technical-route.md` | `docs/decisions/ADR-005-backend-technical-route.md`、`README.md` | 负责后端实现基线与部署定位 |
| 正式评分主线 | `docs/architecture/layered-rubric-evaluation-architecture.md` | `docs/decisions/ADR-004-layered-rubric-evaluation.md`、`docs/architecture/scoring-pipeline.md` | 负责正式阶段顺序与职责 |
| 应用层职责边界 | `docs/architecture/application-layer-boundaries.md` | `docs/architecture/scoring-pipeline.md`、`docs/architecture/provider-abstraction.md` | 负责后端目录职责 |
| API 资源与接口语义 | `apps/api/contracts/api-v0-overview.md` | `docs/contracts/frontend-minimal-api-assumptions.md` | 负责对外 API v0 |
| 任务状态与错误语义 | `apps/api/contracts/job-lifecycle-and-error-semantics.md` | `docs/architecture/frontend-task-and-state-flow.md` | 负责状态与错误真源 |
| 正式结果结构语义 | `docs/contracts/json-contracts.md` | `packages/schemas/` | 文档解释语义，结构真源在 Schema |
| 阶段中间结构语义 | `docs/contracts/rubric-stage-contracts.md` | `docs/architecture/layered-rubric-evaluation-architecture.md` | 负责中间阶段对象含义 |
| Schema 治理规则 | `docs/contracts/schema-versioning-policy.md` | `packages/schemas/README.md` | 负责版本与兼容性规则 |
| Prompt 生命周期与治理 | `docs/prompting/prompt-lifecycle.md` | `prompts/README.md` | 负责 Prompt 资产生命周期 |
| Provider 抽象边界 | `docs/architecture/provider-abstraction.md` | `docs/architecture/application-layer-boundaries.md` | 负责供应商适配边界 |
| 集成边界 | `docs/architecture/integration-boundaries.md` | `docs/architecture/application-layer-boundaries.md`、`apps/api/contracts/api-v0-overview.md` | 负责跨模块交互边界 |
| 本地开发与部署拓扑 | `docs/operations/local-development-topology.md` | `docs/architecture/system-overview.md`、`docs/architecture/backend-technical-route.md` | 负责本机运行关系说明 |
| Evals 组织与回归规则 | `evals/README.md` | `docs/architecture/evals-framework.md` | 负责最小回归闭环 |
| 前端总览与主流程 | `docs/architecture/frontend-overview.md` | `docs/architecture/frontend-information-architecture.md` | 负责前端整体入口 |
| 前端状态流 | `docs/architecture/frontend-task-and-state-flow.md` | `apps/api/contracts/job-lifecycle-and-error-semantics.md` | 前后端状态需一致 |
| 前端页面数据模型 | `docs/contracts/frontend-view-models.md` | `docs/contracts/frontend-api-consumption-and-query-strategy.md` | 负责页面消费对象 |
| 前端输入与提交边界 | `docs/contracts/frontend-input-and-submit-spec.md` | `docs/contracts/frontend-backend-boundary.md` | 负责输入页边界 |
| 前后端边界 | `docs/contracts/frontend-backend-boundary.md` | `apps/api/contracts/api-v0-overview.md` | 负责职责边界 |

## 联动更新矩阵

### 更新 `docs/planning/mvp-phase-1-scope.md` 时

至少检查：

- `docs/architecture/backend-technical-route.md`
- `docs/architecture/application-layer-boundaries.md`
- `apps/api/contracts/api-v0-overview.md`
- `evals/README.md`

### 更新 `docs/architecture/layered-rubric-evaluation-architecture.md` 时

至少检查：

- `docs/contracts/rubric-stage-contracts.md`
- `docs/architecture/scoring-pipeline.md`
- `docs/contracts/json-contracts.md`
- `docs/architecture/evals-framework.md`
- `docs/prompting/prompt-lifecycle.md`
- `docs/planning/layered-rubric-implementation-plan.md`

### 更新 `apps/api/contracts/api-v0-overview.md` 时

至少检查：

- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- `packages/schemas/` 对应结构

### 更新 `apps/api/contracts/job-lifecycle-and-error-semantics.md` 时

至少检查：

- `docs/architecture/frontend-task-and-state-flow.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `evals/README.md`

### 更新 `docs/contracts/schema-versioning-policy.md` 时

至少检查：

- `docs/prompting/prompt-lifecycle.md`
- `evals/README.md`
- `packages/schemas/README.md`

### 更新 `docs/prompting/prompt-lifecycle.md` 时

至少检查：

- `prompts/README.md`
- `evals/README.md`
- `docs/contracts/schema-versioning-policy.md`
- `docs/architecture/integration-boundaries.md`

### 更新 `docs/architecture/backend-technical-route.md` 时

至少检查：

- `README.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/application-layer-boundaries.md`
- `docs/architecture/scoring-pipeline.md`
- `docs/architecture/provider-abstraction.md`
- `docs/operations/local-development-topology.md`

### 更新 `docs/architecture/integration-boundaries.md` 时

至少检查：

- `docs/architecture/application-layer-boundaries.md`
- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/schema-versioning-policy.md`
- `docs/prompting/prompt-lifecycle.md`
- `evals/README.md`

## 禁止重复定义的主题

以下主题不应在多个文档中分别定义独立规则：

- 任务状态枚举
- 结果状态枚举
- 正式结果核心字段语义
- Prompt 生命周期阶段
- 正式评分主线阶段名称
- Schema 兼容性定义
- Phase 1 范围边界

## 完成标准

满足以下条件时，可认为文档覆盖矩阵有效：

- 团队能快速判断某个问题该看哪份文档
- 新增文档时不再与既有文档重复抢定义权
- 更新关键文档时知道需要联动检查哪些文档
