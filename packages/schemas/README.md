# `packages/schemas`

## 模块角色

该模块是当前仓库正式结构契约的唯一目标真源目录。

当前阶段采用以下判定规则：

- 已经落地的 schema 类，以本目录下对应 `.py` 文件为唯一正式结构真源
- 尚未落地的对象，仅由 `docs/contracts/canonical-schema-index.md` 临时承担对象级索引职责
- README 只负责模块边界说明，不替代正式 schema 类

## 当前子域

- `common/`：共享枚举、基础模型与跨对象复用校验
- `input/`：输入对象与任务创建请求相关 schema
- `output/`：任务对象、结果对象、错误与 envelope 相关 schema
- `stages/`：评分主线阶段对象相关 schema
- `evals/`：评测样本、记录、基线、报告相关 schema（当前仍未落地 `.py`）

## 主要职责

- 承载正式 schema 文件
- 固化字段命名、类型、枚举与必需性
- 为 API 边界、worker、evals 和 Prompt 输出提供统一目标结构
- 为版本治理与兼容性判断提供唯一依据

## 不负责

- 定义 API 路径
- 定义页面 View Model
- 定义 Prompt 生命周期
- 承担运行时编排逻辑

## 输入依赖

当前上游真源文档：

- `docs/contracts/canonical-schema-index.md`
- `docs/architecture/domain-model.md`
- `docs/contracts/json-contracts.md`
- `docs/contracts/rubric-stage-contracts.md`
- `docs/contracts/schema-versioning-policy.md`

## 下游消费者

- `apps/api/`
- `packages/application/`
- `apps/worker/`
- `evals/`
- `packages/prompt-runtime/`

## 当前落地状态

当前已经实际落地：

- `common/`
  - `SchemaModel`
  - `MetaData`
  - 共享枚举与校验工具
- `input/`
  - `ManuscriptChapter`
  - `ManuscriptOutline`
  - `Manuscript`
  - `JointSubmissionRequest`
  - `InputScreeningResult`
- `output/`
  - `EvaluationTask`
  - `EvaluationTaskSummary`
  - `RecentResultSummary`
  - `DashboardSummary`
  - `HistoryList`
  - `PlatformRecommendation`
  - `DetailedAnalysis`
  - `FinalEvaluationProjection`
  - `EvaluationResult`
  - `EvaluationResultResource`
  - `ErrorObject`
  - `SuccessEnvelope`
  - `ErrorEnvelope`
- `stages/`
  - `RubricEvaluationEvidenceRef`
  - `RubricEvaluationItem`
  - `RubricEvaluationSet`
  - `ConsistencyConflict`
  - `ConsistencyCheckResult`
  - `AggregatedRubricResult`

当前仍未落地：

- `evals/` 相关正式 schema 类
- 与多租户/多用户相关的扩展结构

## 错误语义

- `packages/schemas/` 只定义结构，不单独发明业务状态含义
- 状态枚举、结果状态和错误码语义必须与主文档保持一致
- 若 schema 变化影响这些共享字段，必须同步更新上游治理文档

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "implemented|schema_pending|input/|output/|stages/|evals/" docs/contracts/canonical-schema-index.md packages/schemas/README.md`

## DevFleet 使用约束

- 任何落地 schema 的 mission 都必须先读 `docs/contracts/canonical-schema-index.md`
- 不允许在 `apps/api`、前端假契约或 `evals/` 文档中越权发明正式字段结构
- `packages/schemas/evals/README.md` 当前不是已实现证明；只有新增 `.py` schema 类才算正式落地
