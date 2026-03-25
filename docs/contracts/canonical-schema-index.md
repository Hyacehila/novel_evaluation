# Canonical Schema Index

## 文档目的

本文档是当前仓库结构真源的对象级索引入口，用于回答：

- 某个对象当前是否已经有正式 schema 类
- 若已落地，正式真源文件在哪里
- 若尚未落地，将来应落到哪个子域
- 哪份文档负责解释该对象的业务语义
- 哪些目录目前只有 README 占位，不能被误认成已实现

本文档不替代正式 schema 文件；它负责索引、归类、状态标记和真源绑定。

## 状态词表

- `implemented`：正式 schema 类已存在，结构真源以 `packages/schemas/**/*.py` 为准
- `doc_frozen`：对象语义已冻结，可作为 mission 输入真源
- `schema_pending`：对象已经冻结，但正式 schema 类尚未落地
- `reserved`：保留位或未来扩展对象，不作为当前实现起点

补充约束：

- 仅有 README 或目录占位不算 `implemented`
- 若对象已 `implemented`，则不再标记 `schema_pending`

## 真源优先级

当前阶段按以下顺序判定结构真源：

1. `packages/schemas/` 中已经实际落地的正式 schema 类
2. 本文档 `Canonical Schema Index`（仅用于尚未落地对象的索引与路径绑定）
3. `docs/contracts/json-contracts.md`
4. `docs/contracts/rubric-stage-contracts.md`
5. `docs/architecture/domain-model.md`
6. API / 前端 / Evals 消费文档

说明：

- 若同一对象已在 `packages/schemas/` 落地，则以对应 `.py` 文件为唯一正式结构真源
- API 文档、前端假契约、README 和 Evals 文档都不得反向定义第二套正式字段结构

## 对象分类

### 一、共享基础对象

| 对象 | 当前状态 | 正式真源文件 | 语义主文档 | 主要消费者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `SchemaModel` | `implemented` | `packages/schemas/common/base.py` | `docs/contracts/schema-versioning-policy.md` | 全部 schema 子域 | 统一 `extra="forbid"` 与冻结模型配置 |
| `MetaData` | `implemented` | `packages/schemas/common/base.py` | `apps/api/contracts/api-v0-overview.md` | API、frontend、history | 分页与响应元信息对象 |

### 二、输入与任务对象

| 对象 | 当前状态 | 正式真源文件 | 语义主文档 | 主要消费者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `ManuscriptChapter` | `implemented` | `packages/schemas/input/manuscript.py` | `docs/architecture/domain-model.md` | application、API | 正文章节对象 |
| `ManuscriptOutline` | `implemented` | `packages/schemas/input/manuscript.py` | `docs/architecture/domain-model.md` | application、API | 大纲对象 |
| `Manuscript` | `implemented` | `packages/schemas/input/manuscript.py` | `docs/architecture/domain-model.md` | application、API、worker | 联合投稿包领域对象 |
| `JointSubmissionRequest` | `implemented` | `packages/schemas/input/joint_submission.py` | `docs/contracts/json-contracts.md`、`apps/api/contracts/api-v0-overview.md` | API、frontend adapter | 创建任务请求对象 |
| `InputScreeningResult` | `implemented` | `packages/schemas/input/screening.py` | `docs/contracts/rubric-stage-contracts.md` | application、prompt-runtime、evals | 输入预检查结果当前落在 `input/` 子域 |
| `EvaluationTask` | `implemented` | `packages/schemas/output/task.py` | `docs/architecture/domain-model.md`、`apps/api/contracts/job-lifecycle-and-error-semantics.md` | API、frontend、worker | 任务对象是状态语义主承载体 |
| `EvaluationTaskSummary` | `implemented` | `packages/schemas/output/task.py` | `apps/api/contracts/api-v0-overview.md` | dashboard、history | 摘要对象，不替代详情对象 |
| `RecentResultSummary` | `implemented` | `packages/schemas/output/task.py` | `apps/api/contracts/api-v0-overview.md` | dashboard | 最近结果摘要对象 |
| `DashboardSummary` | `implemented` | `packages/schemas/output/dashboard.py` | `apps/api/contracts/api-v0-overview.md` | frontend、API | 工作台首页摘要聚合对象 |
| `HistoryList` | `implemented` | `packages/schemas/output/dashboard.py` | `apps/api/contracts/api-v0-overview.md` | frontend、API | 历史记录列表对象 |

### 三、阶段契约对象

| 对象 | 当前状态 | 正式真源文件 | 语义主文档 | 主要消费者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `RubricEvaluationEvidenceRef` | `implemented` | `packages/schemas/stages/rubric.py` | `docs/contracts/rubric-stage-contracts.md` | application、evals | 证据引用对象 |
| `RubricEvaluationItem` | `implemented` | `packages/schemas/stages/rubric.py` | `docs/contracts/rubric-stage-contracts.md` | application、aggregation、evals | 单项 rubric 结果 |
| `RubricEvaluationSet` | `implemented` | `packages/schemas/stages/rubric.py` | `docs/contracts/rubric-stage-contracts.md` | consistency、aggregation、evals | 新 `8` 轴主干对象 |
| `ConsistencyConflict` | `implemented` | `packages/schemas/stages/consistency.py` | `docs/contracts/rubric-stage-contracts.md` | consistency、aggregation、evals | 冲突对象 |
| `ConsistencyCheckResult` | `implemented` | `packages/schemas/stages/consistency.py` | `docs/contracts/rubric-stage-contracts.md` | aggregation、evals | 一致性整理输出 |
| `AggregatedRubricResult` | `implemented` | `packages/schemas/stages/aggregation.py` | `docs/contracts/rubric-stage-contracts.md` | result projection、evals | 聚合输出对象 |
| `FinalEvaluationProjection` | `implemented` | `packages/schemas/output/result.py` | `docs/contracts/rubric-stage-contracts.md`、`docs/contracts/json-contracts.md` | API、frontend、evals | 对外正式结果前的最后投影层 |

### 四、正式结果与错误对象

| 对象 | 当前状态 | 正式真源文件 | 语义主文档 | 主要消费者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `PlatformRecommendation` | `implemented` | `packages/schemas/output/result.py` | `docs/contracts/json-contracts.md` | frontend、evals | 平台推荐对象 |
| `DetailedAnalysis` | `implemented` | `packages/schemas/output/result.py` | `docs/contracts/json-contracts.md` | frontend、evals | 详细分析对象 |
| `EvaluationResult` | `implemented` | `packages/schemas/output/result.py` | `docs/contracts/json-contracts.md`、`docs/architecture/domain-model.md` | API、frontend、evals | 正式结果正文对象 |
| `EvaluationResultResource` | `implemented` | `packages/schemas/output/result.py` | `apps/api/contracts/api-v0-overview.md` | API、frontend | 结果资源对象，区分 `available / not_available / blocked` |
| `ErrorObject` | `implemented` | `packages/schemas/output/error.py` | `apps/api/contracts/job-lifecycle-and-error-semantics.md` | API、frontend、evals | 错误对象结构 |
| `SuccessEnvelope` | `implemented` | `packages/schemas/output/envelope.py` | `apps/api/contracts/api-v0-overview.md` | API、frontend | 成功响应 envelope |
| `ErrorEnvelope` | `implemented` | `packages/schemas/output/envelope.py` | `apps/api/contracts/api-v0-overview.md` | API、frontend | 失败响应 envelope |

### 五、评测与回归对象

| 对象 | 当前状态 | 目标正式真源目录 | 语义主文档 | 主要消费者 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `EvalCase` | `doc_frozen` + `schema_pending` | `packages/schemas/evals/` | `evals/cases/README.md`、`evals/README.md` | evals runner | 结构化评测用例 |
| `EvalRecord` | `doc_frozen` + `schema_pending` | `packages/schemas/evals/` | `evals/runners/README.md`、`evals/README.md` | evals runner、reports | 单次评测记录 |
| `EvalBaseline` | `doc_frozen` + `schema_pending` | `packages/schemas/evals/` | `evals/baselines/README.md`、`evals/README.md` | evals runner、reports | 基线记录 |
| `EvalReport` | `doc_frozen` + `schema_pending` | `packages/schemas/evals/` | `evals/reports/README.md`、`evals/README.md` | reports、quality gate | 回归报告对象 |

补充说明：

- `packages/schemas/evals/` 当前只有 `README.md`，没有正式 `.py` schema 类
- 因此 Evals 相关对象仍处于 `doc_frozen + schema_pending`，不能误标为 `implemented`

## 字段级治理要求

以下字段或元信息属于跨对象共享约束，任何对象一旦使用，就必须保持同一语义：

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `inputComposition`
- `evaluationMode`
- `status`
- `resultStatus`
- `errorCode`
- `errorMessage`

说明：

- 这些字段的语义不得由消费文档单独扩写
- 若要变更这些字段，必须同步更新：
  - `docs/contracts/schema-versioning-policy.md`
  - `apps/api/contracts/job-lifecycle-and-error-semantics.md`
  - `docs/contracts/frontend-minimal-api-assumptions.md`
  - `evals/README.md`

## 当前仍未冻结到正式文件级的部分

当前仍然没有正式 `.py` 文件落地的只有：

- `packages/schemas/evals/` 下的 `EvalCase / EvalRecord / EvalBaseline / EvalReport`
- 多用户相关扩展字段（如 `ownerRef / userId / workspaceId / tenantId`）

以下部分已经冻结到文件级，不再视为未定：

- `packages/schemas/input/` 下的输入对象文件
- `packages/schemas/output/` 下的 `task / result / error / envelope / dashboard` 拆分
- `packages/schemas/stages/` 目录与 `rubric / consistency / aggregation` 拆分

## DevFleet 使用规则

在 `DevFleet-Ready` 阶段，任何实现型 mission 都必须遵守：

- 若对象已 `implemented`，只能以对应 `.py` 文件为正式结构真源
- 若对象仍为 `schema_pending`，只能消费本文给出的目标目录与语义绑定
- 若需要新增对象，必须先修改本文，再修改实现
- 不允许在 API DTO、前端假契约、README 或 Evals 文档中越权引入新正式对象

## 待确认项

以下内容在当前阶段允许保留为待确认项，但必须显式记录，不能由实现阶段暗中决定：

- 多用户场景下是否需要 `ownerRef / userId / workspaceId / tenantId`
- `packages/schemas/evals/` 中正式文件的命名颗粒度
- `EvalReport` 是否拆成基线报告与比较报告两类正式结构

## 与现有文档的关系

- 领域对象语义见 `docs/architecture/domain-model.md`
- 对外结果语义见 `docs/contracts/json-contracts.md`
- 阶段契约语义见 `docs/contracts/rubric-stage-contracts.md`
- Schema 治理规则见 `docs/contracts/schema-versioning-policy.md`
- API 资源边界见 `apps/api/contracts/api-v0-overview.md`
