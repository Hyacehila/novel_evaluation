# 面向网络小说双输入全 LLM Rubric 阶段契约

## 适用主线

正式评分主线固定为：

1. `input_screening`
2. `rubric_evaluation`
3. `consistency_check`
4. `aggregation`
5. `final_projection`

## 共享枚举

### `stage`

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

### `inputComposition`

- `chapters_outline`
- `chapters_only`
- `outline_only`

### `evaluationMode`

- `full`
- `degraded`

### `axisId`

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

## `InputScreeningResult`

关键字段：

- `chaptersSufficiency`
- `outlineSufficiency`
- `evaluationMode`
- `rateable`
- `continueAllowed`
- `rejectionReasons`
- `riskTags`
- `segmentationPlan`

约束：

- `full` 模式只允许在 `chapters_outline` 且两侧 `sufficient` 时出现
- `rateable=false` 时必须给出 `rejectionReasons`
- 当前 schema 只要求 `segmentationPlan` 是对象或 `null`；调用方不得依赖其内部固定键名
- 当前主链实现里 `segmentationPlan` 允许为 `null`

## `RubricEvaluationSlice`

当前 `rubric_evaluation` 先按切片执行，再合并为完整集合。

关键字段：

- `requestedAxes`
- `items`
- `axisSummaries`
- `missingRequiredAxes`
- `overallConfidence`

约束：

- `items` 必须完整且唯一覆盖 `requestedAxes`
- `axisSummaries` 只能且必须覆盖 `requestedAxes`
- `missingRequiredAxes` 只能引用 `requestedAxes` 内的轴

## `RubricEvaluationSet`

关键字段：

- `items`
- `axisSummaries`
- `missingRequiredAxes`
- `riskTags`
- `overallConfidence`

约束：

- `items` 必须覆盖全部 `8` 轴
- `axisSummaries` 必须覆盖全部 `8` 轴
- `degraded` 模式仍要输出全部 `8` 轴，只能通过 `degradedByInput / riskTags / confidence` 表达受限

## `ConsistencyCheckResult`

关键字段：

- `passed`
- `conflicts`
- `crossInputMismatchDetected`
- `unsupportedClaimsDetected`
- `duplicatedPenaltiesDetected`
- `missingRequiredAxes`
- `normalizationNotes`
- `confidence`
- `continueAllowed`

约束：

- 只负责整理与冲突识别
- `continueAllowed=false` 时进入业务阻断，而不是伪低分结果
- `conflicts` 当前可能包含：
  - `cross_input_mismatch`
  - `unsupported_claim`
  - `duplicated_penalty`
  - `missing_required_axis`
  - `weak_evidence`

## `AggregatedRubricResult`

关键字段：

- `overallVerdictDraft`
- `overallSummaryDraft`
- `platformCandidates`
- `marketFitDraft`
- `riskTags`
- `overallConfidence`

约束：

- 聚合阶段当前直接输出正式结果草案字段
- 不再把旧四维骨架作为正式阶段 schema 输出

## `FinalEvaluationProjection`

作用：

- 作为对外 `EvaluationResult` 前的最后内部投影层

关键字段：

- `axes`
- `overall`

约束：

- `axes` 必须完整覆盖全部 `8` 轴
- `overall` 只包含 `score / verdict / summary / platformCandidates / marketFit`
- 不新增额外执行追踪字段
- 执行追踪统一进入 `EvalRecord` 与日志
- `blocked` 或 `not_available` 场景不创建伪 projection

## 文件归属

- `InputScreeningResult` 位于 `packages/schemas/input/screening.py`
- 其它阶段对象位于 `packages/schemas/stages/`
- 最终投影与正式结果对象位于 `packages/schemas/output/result.py`
