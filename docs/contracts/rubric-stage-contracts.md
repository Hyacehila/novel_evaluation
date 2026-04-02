# 面向网络小说双输入全 LLM Rubric 阶段契约

## 适用主线

正式评分主线固定为：

1. `input_screening`
2. `type_classification`
3. `rubric_evaluation`
4. `type_lens_evaluation`
5. `consistency_check`
6. `aggregation`
7. `final_projection`

## 共享枚举

### `stage`

- `input_screening`
- `type_classification`
- `rubric_evaluation`
- `type_lens_evaluation`
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

### `novelType`

- `female_general`
- `fantasy_upgrade`
- `urban_reality`
- `history_military`
- `sci_fi_apocalypse`
- `suspense_horror`
- `game_derivative`
- `general_fallback`

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
- 当前 schema 只要求 `segmentationPlan` 是对象或 `null`

## `TypeClassificationResult`

关键字段：

- `candidates`
- `novelType`
- `classificationConfidence`
- `fallbackUsed`
- `summary`

约束：

- `candidates` 必须固定输出 `Top-3`
- 候选类型不允许重复
- 非 fallback 场景下，`novelType` 必须来自候选集合
- `classificationConfidence` 当前取最终选定逻辑所依据的首位置信度

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

## `TypeLensEvaluationResult`

关键字段：

- `novelType`
- `summary`
- `items`
- `overallConfidence`

约束：

- `items` 必须完整覆盖当前 `novelType` 对应的固定 `4` 个 lens
- `items` 不允许重复 lensId
- 每个 `TypeLensItem` 至少包含一条 `evidenceRefs`
- `degraded` 模式仍输出完整 `4` 个 lens，只通过 `degradedByInput / confidence` 表达受限

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

- 当前为本地整理阶段，不额外调用 provider
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
- `verdictSubQuote`
- `overallSummaryDraft`
- `platformCandidates`
- `marketFitDraft`
- `strengthCandidates`
- `weaknessCandidates`
- `riskTags`
- `overallConfidence`

约束：

- 聚合阶段输入固定来自 `screening + type_classification + rubric + type_lens + consistency`
- `platformCandidates` 使用结构化对象，而非字符串数组
- 若存在平台候选，权重和必须为 `100`

## `FinalEvaluationProjection`

作用：

- 作为对外 `EvaluationResult` 前的最后内部投影层

关键字段：

- `axes`
- `overall`
- `typeAssessment`

约束：

- `axes` 必须完整覆盖全部 `8` 轴
- `overall` 当前包含：
  - `score`
  - `verdict`
  - `verdictSubQuote`
  - `summary`
  - `platformCandidates`
  - `marketFit`
  - `strengths`
  - `weaknesses`
- `typeAssessment` 当前可为空，用于兼容历史结果读取
- `blocked` 或 `not_available` 场景不创建伪 projection

## 文件归属

- `InputScreeningResult` 位于 `packages/schemas/input/screening.py`
- `TypeClassificationResult` 位于 `packages/schemas/stages/type_classification.py`
- `RubricEvaluationSet` 位于 `packages/schemas/stages/rubric.py`
- `TypeLensEvaluationResult` 位于 `packages/schemas/stages/type_lens.py`
- `ConsistencyCheckResult` 位于 `packages/schemas/stages/consistency.py`
- `AggregatedRubricResult` 位于 `packages/schemas/stages/aggregation.py`
- 最终投影与正式结果对象位于 `packages/schemas/output/result.py`
