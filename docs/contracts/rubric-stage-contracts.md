# 面向网络小说双输入全 LLM Rubric 阶段契约

## 文档角色

本文档冻结正式评分主线中的中间阶段对象，用于支撑：

- `packages/application/` 的用例编排
- `packages/schemas/` 的后续正式 schema 落位
- `apps/api/`、`apps/worker/`、`evals/` 对阶段结果的统一理解
- DevFleet 在后续实现阶段对输入、输出和错误边界的单一引用

本文档不替代正式 schema 文件；它负责冻结对象语义、枚举、字段和强约束。

## 适用主线

正式评分主线固定为：

1. 输入预检查
2. `LLM rubric` 分点评价
3. 轻量一致性整理
4. 新模型聚合输出
5. 正式结果投影

说明：

- 不再保留 `pairwise`、多路径裁决、外部仲裁或并行评分主线
- 所有阶段对象都服务同一条双输入单主线

## 共享枚举

### 阶段名 `stage`

冻结枚举：

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

### 输入组成 `inputComposition`

冻结枚举：

- `chapters_outline`
- `chapters_only`
- `outline_only`

### 评估模式 `evaluationMode`

冻结枚举：

- `full`
- `degraded`

### 输入充分性 `sufficiency`

冻结枚举：

- `sufficient`
- `insufficient`
- `missing`

### 阶段状态 `stageStatus`

冻结枚举：

- `ok`
- `warning`
- `failed`
- `unrateable`

### 证据来源 `sourceType`

冻结枚举：

- `chapters`
- `outline`
- `cross_input`

### 评分档位 `scoreBand`

冻结枚举：

- `0`
- `1`
- `2`
- `3`
- `4`

## 共享字段

### 标识与版本字段

除非对象明确豁免，阶段对象默认继承：

- `taskId`
- `stage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`

### 上下文字段

除非对象明确豁免，阶段对象默认继承：

- `inputComposition`
- `evaluationMode`
- `hasChapters`
- `hasOutline`

### 质量字段

除非对象明确豁免，阶段对象默认继承：

- `status`
- `confidence`
- `riskTags`
- `issues`

约束：

- `confidence` 必须是 `0-1` 之间的小数
- `issues` 用于记录结构化问题，不允许退化为大段说明文

## 固定词表

### 新 `8` 轴主评价层 `axisId`

冻结词表：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

### 旧四维骨架层 `skeletonDimensionId`

冻结词表：

- `marketAttraction`
- `narrativeExecution`
- `characterMomentum`
- `noveltyUtility`

### 风险词表 `fatalRisk`

当前冻结最小词表：

- `aiManualTone`
- `staleFormula`
- `conceptSpam`
- `fakePayoff`
- `nonNarrativeSubmission`
- `insufficientMaterial`

## 阶段对象

### 1. `InputScreeningResult`

用途：

- 判断输入是否可进入正式主线
- 冻结输入组成、输入充分性和降级语义
- 为下游阶段提供结构化上下文

冻结字段：

- `taskId`
- `stage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `inputComposition`
- `hasChapters`
- `hasOutline`
- `chaptersSufficiency`
- `outlineSufficiency`
- `evaluationMode`
- `rateable`
- `status`
- `rejectionReasons`
- `riskTags`
- `segmentationPlan`
- `confidence`
- `continueAllowed`

字段约束：

- `stage` 固定为 `input_screening`
- `chaptersSufficiency` / `outlineSufficiency` 使用 `sufficiency` 冻结枚举
- `rateable` 表示业务语义上是否可继续评分
- `continueAllowed` 表示是否允许进入下游阶段
- `segmentationPlan` 只描述长文本处理边界，不得扩展成第二套评分路由

强约束：

- `evaluationMode=full` 当且仅当：
  - `inputComposition=chapters_outline`
  - `chaptersSufficiency=sufficient`
  - `outlineSufficiency=sufficient`
- `evaluationMode=degraded` 用于单侧输入仍可继续评估的场景
- `rateable=false` 时，不允许伪造低分结果替代阻断结论
- `rateable=false` 且阶段正常结束时，应落到 `EvaluationTask(status=completed, resultStatus=blocked)`
- 只有阶段执行本身异常时，才进入 `failed + not_available`

### 2. `RubricEvaluationEvidenceRef`

用途：

- 表示单个分点评价项的证据引用

冻结字段：

- `sourceType`
- `sourceSpan`
- `excerpt`
- `observationType`
- `evidenceNote`
- `confidence`

强约束：

- `sourceType` 只能取 `chapters`、`outline`、`cross_input`
- `sourceSpan` 应优先使用结构化范围，而不是自由文本位置描述
- `excerpt` 只用于内部治理、回归和审查，不默认暴露到正式结果对象

### 3. `RubricEvaluationItem`

用途：

- 表示单个正式 `rubric` 评价项

冻结字段：

- `evaluationId`
- `axisId`
- `scoreBand`
- `reason`
- `evidenceRefs`
- `confidence`
- `riskTags`
- `blockingSignals`
- `affectedSkeletonDimensions`
- `degradedByInput`

强约束：

- `axisId` 必须属于冻结的 `8` 轴词表
- `scoreBand` 使用固定 `0-4` 档位
- 每个评价项至少包含一条 `evidenceRefs`
- 无依据时不得输出高分
- 命中高风险信号时，必须在 `riskTags` 或 `blockingSignals` 中显式记录
- `affectedSkeletonDimensions` 只能引用冻结的骨架层词表

### 4. `RubricEvaluationSet`

用途：

- 汇总全部 `RubricEvaluationItem`
- 作为一致性整理与聚合的标准输入对象

冻结字段：

- `taskId`
- `stage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `inputComposition`
- `evaluationMode`
- `items`
- `axisSummaries`
- `missingRequiredAxes`
- `riskTags`
- `overallConfidence`

强约束：

- `stage` 固定为 `rubric_evaluation`
- `items` 必须覆盖全部 `8` 轴
- `full` 模式下：
  - 不允许缺轴
  - `missingRequiredAxes` 必须为空数组
- `degraded` 模式下：
  - 仍然输出全部 `8` 轴评价项
  - 受输入缺失影响的轴必须通过 `degradedByInput`、较低 `confidence` 或 `blockingSignals` 显式表达
  - 不允许静默省略受影响轴

### 5. `ConsistencyConflict`

用途：

- 表示轻量一致性整理中识别到的具体冲突或归一化问题

冻结字段：

- `conflictId`
- `conflictType`
- `relatedEvaluationIds`
- `description`
- `severity`
- `normalizationNote`

`conflictType` 当前冻结枚举：

- `cross_input_mismatch`
- `unsupported_claim`
- `duplicated_penalty`
- `missing_required_axis`
- `weak_evidence`

### 6. `ConsistencyCheckResult`

用途：

- 记录轻量一致性整理结果
- 决定聚合是否允许继续消费上游评价结果

冻结字段：

- `taskId`
- `stage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `inputComposition`
- `evaluationMode`
- `passed`
- `conflicts`
- `crossInputMismatchDetected`
- `unsupportedClaimsDetected`
- `duplicatedPenaltiesDetected`
- `missingRequiredAxes`
- `normalizationNotes`
- `confidence`
- `continueAllowed`

强约束：

- `stage` 固定为 `consistency_check`
- 本阶段只负责整理与冲突识别，不负责重新评分
- `continueAllowed=false` 时，不允许下游聚合产出伪正式结果正文
- `crossInputMismatchDetected=true` 且冲突不可归一化时，应进入阻断语义，而不是低分替代

### 7. `AggregatedRubricResult`

用途：

- 将 `8` 轴结果汇总到旧四维骨架层
- 生成对外结果草案所需的内部聚合对象

冻结字段：

- `taskId`
- `stage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `axisScores`
- `skeletonScores`
- `topLevelScoresDraft`
- `strengthCandidates`
- `weaknessCandidates`
- `platformCandidates`
- `marketFitDraft`
- `editorVerdictDraft`
- `detailedAnalysisDraft`
- `supportingAxisMap`
- `supportingSkeletonMap`
- `riskTags`
- `overallConfidence`

强约束：

- `stage` 固定为 `aggregation`
- `topLevelScoresDraft` 只是内部草案，不等于 API 正式返回体
- `commercialValue` 主要受 `marketAttraction` 影响，并次级参考 `characterMomentum`
- `writingQuality` 主要受 `narrativeExecution` 影响，并次级参考 `characterMomentum`
- `innovationScore` 主要受 `noveltyUtility` 影响
- `signingProbability` 不允许脱离其它顶层分数、`platformFit` 和 `fatalRisk` 独立飙升
- 聚合层不得绕过 `RubricEvaluationSet` 整体直评

### 8. `FinalEvaluationProjection`

用途：

- 生成对外正式结果对象前的最后内部投影层

冻结字段：

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`
- `strengths`
- `weaknesses`
- `platforms`
- `marketFit`
- `editorVerdict`
- `detailedAnalysis`
- `overallConfidence`
- `supportingAxisMap`
- `supportingSkeletonMap`

强约束：

- `stage` 语义固定为 `final_projection`
- 该对象只在可以形成正式结果正文时生成
- `blocked` 或 `not_available` 场景不创建伪 `FinalEvaluationProjection`
- `supportingAxisMap` 与 `supportingSkeletonMap` 属于内部追踪字段，不要求前端直接消费

## 阻断与失败边界

- `InputScreeningResult.rateable=false` 且阶段正常结束：进入业务阻断，任务语义为 `completed + blocked`
- `ConsistencyCheckResult.continueAllowed=false` 且属于不可归一化冲突：进入业务阻断，任务语义为 `completed + blocked`
- Provider 故障、超时、结构校验失败、阶段执行崩溃：进入技术失败，任务语义为 `failed + not_available`

## 与正式结果的关系

- 阶段对象是后端内部治理对象，不直接等于对外 API DTO
- 对外 `EvaluationResult` 语义见 `docs/contracts/json-contracts.md`
- 任务状态与结果状态语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`

## 当前待确认项

以下内容当前保留为待确认项，不由实现阶段暗中决定：

- `segmentationPlan` 的最终正式字段颗粒度
- 阶段对象是否在 `packages/schemas/stages/` 下独立落位
- `FinalEvaluationProjection` 是否需要额外最小元信息字段

## 完成标准

满足以下条件时，可认为阶段契约足以支撑 DevFleet 后续实现 mission：

- 不再停留在“大面积建议字段”层级
- 输入充分性、降级和阻断边界已冻结
- `8` 轴、骨架层和正式结果投影之间的责任已清楚分层
- 上游任务可以按本文档独立实现而不再反复追问字段语义
