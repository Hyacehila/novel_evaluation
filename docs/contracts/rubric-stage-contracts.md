# 全 LLM Rubric 阶段契约

## 目标

本文档定义全 `LLM` 分阶段 `rubric` 评分流程中的中间阶段契约，用于指导后续在 `packages/schemas/` 中落地正式结构定义。

本文档只负责说明结构含义、边界和映射关系，不代替正式 Schema 本体。

## 契约分层原则

### 1. 对外结果契约与对内阶段契约分离

- 对外正式结果继续使用统一结果结构
- 对内阶段契约用于承接评分过程中的结构化中间产物
- 前端只消费正式结果对象，不直接依赖阶段契约

### 2. 所有阶段输出都应是严格 JSON

即使是内部阶段对象，也应满足：

- 结构可解析
- 字段含义稳定
- 无 JSON 外自然语言
- 版本可追踪

### 3. 契约必须服务单主线评分流程

所有阶段对象都应服务以下正式主线：

1. `输入预检查`
2. `LLM rubric 分点评价`
3. `轻量一致性整理`
4. `新模型聚合输出`
5. `正式结果投影`

文档中不再保留分叉升级、外部介入或并行评分路径相关阶段对象。

### 4. 置信度与错误语义必须显式化

每个阶段对象都应显式表达：

- 置信度
- 是否可继续进入下游
- 当前失败是结构失败、不可评失败还是判断失败

## 通用字段约定

### 标识字段

- `taskId`：一次评分任务的唯一标识
- `stage`：当前阶段名称
- `schemaVersion`：阶段结构版本
- `rubricVersion`：本阶段使用的 Rubric 版本
- `promptVersion`：本阶段使用的 Prompt 版本
- `providerId`：模型供应商标识
- `modelId`：模型标识

说明：

- 当前正式主线默认由 `LLM` 生成评分阶段对象
- 系统边界的确定性校验不属于本文档的阶段对象范围

### 质量字段

- `confidence`：`0-1` 之间的小数
- `status`：建议使用 `ok`、`warning`、`failed`、`unrateable`
- `issues`：当前阶段发现的问题列表
- `riskTags`：当前阶段命中的风险标签列表

### 证据引用字段

为了避免“证据抽取”与“评分项”分离导致的双重治理，正式主线采用内嵌证据引用：

- `sourceSpan`：原文范围引用
- `excerpt`：短摘录，仅用于内部治理与评测
- `observationType`：观察类别
- `evidenceNote`：对该证据的短说明

说明：

- `excerpt` 不应默认进入对外正式结果
- 证据引用应优先使用结构化范围，而不是松散自然语言描述
- 同一阶段对象可复用多个证据引用，不要求再维护独立 `EvidencePack`

## 阶段对象定义

说明：

- 下列“建议字段”主要列出每个阶段对象的业务字段
- 除非明确豁免，每个阶段对象默认还应继承前文定义的标识字段与质量字段

### 1. `InputScreeningResult`

用途：

- 判断输入是否可评
- 识别输入类型与边界风险
- 给后续分点评价阶段提供输入上下文

建议字段：

- `rateable`
- `manuscriptType`：`opening`、`chapter`、`outline`、`other`
- `language`
- `lengthBucket`
- `rejectionReasons`
- `riskTags`
- `segmentationPlan`
- `confidence`

说明：

- `rateable=false` 时，应优先进入结构化失败路径，而不是伪造评分结果
- `segmentationPlan` 用于说明长文本的处理边界，不应演化为额外路由系统

### 2. `RubricEvaluationEvidenceRef`

用途：

- 表示单个分点评价项所依赖的文本依据

建议字段：

- `sourceSpan`
- `excerpt`
- `observationType`
- `evidenceNote`
- `confidence`

### 3. `RubricEvaluationItem`

用途：

- 表示一个稳定的 `rubric` 子维度评价结果

建议字段：

- `evaluationId`
- `dimensionId`
- `subdimensionId`
- `scoreBand`：`0-4`
- `reason`
- `evidenceRefs`：`RubricEvaluationEvidenceRef[]`
- `confidence`
- `riskTags`
- `blockingSignals`

约束：

- 无依据时不得直接输出高分
- `reason` 应短而明确，不应输出长段抒情文本
- 命中高风险信号时，必须输出对应 `riskTags` 或 `blockingSignals`

### 4. `RubricEvaluationSet`

用途：

- 聚合全部 `RubricEvaluationItem`
- 作为轻量一致性整理与聚合模型的标准输入

建议字段：

- `items`：`RubricEvaluationItem[]`
- `dimensionSummaries`
- `coverageByDimension`
- `missingRequiredItems`
- `riskTags`
- `overallConfidence`

说明：

- `RubricEvaluationSet` 是新的评分主干对象
- 该对象同时承接原“证据抽取 + 原子评分”的正式语义
- 文档层不再保留独立 `EvidencePack` 作为长期主阶段对象

## 维度标识符治理

为避免 Prompt、Schema、Evals 与实现层各自发明命名，建议采用以下规则：

- `dimensionId` 与 `subdimensionId` 应作为稳定标识符使用
- 展示名称可以调整，但稳定标识符不应随意重命名
- 重命名稳定标识符应触发版本升级与评测回归
- 文档中出现的一级与二级维度名称，应优先视为正式命名候选

### 5. `ConsistencyConflict`

用途：

- 描述一个具体冲突项或整理项

建议字段：

- `conflictId`
- `conflictType`
- `relatedEvaluations`
- `description`
- `severity`
- `normalizationNote`

### 6. `ConsistencyCheckResult`

用途：

- 记录轻量一致性整理结果
- 为聚合模型提供“哪些项可直接用、哪些项存在问题”的结构化说明

建议字段：

- `passed`
- `conflicts`：`ConsistencyConflict[]`
- `unsupportedClaimsDetected`
- `duplicatedPenaltiesDetected`
- `missingRequiredItems`
- `normalizationNotes`
- `confidence`

说明：

- 本对象不再承担分叉升级或外部介入语义
- 本对象只服务聚合前的结果整理与冲突提示

### 7. `AggregatedRubricResult`

用途：

- 将内部维度结果聚合为对外结果草案
- 生成风险标签、改进重点和顶层评分解释

建议字段：

- `axisScores`
- `topLevelScoresDraft`
- `strengthCandidates`
- `weaknessCandidates`
- `platformCandidates`
- `marketFitDraft`
- `editorVerdictDraft`
- `detailedAnalysisDraft`
- `supportingDimensionMap`
- `riskTags`
- `overallConfidence`

聚合要求：

- 必须记录每个顶层评分主要来自哪些内部维度
- 必须执行基础逻辑校准
- 不允许让 `signingProbability` 独立脱离底层维度飙升
- 聚合模型不得重新绕过分点评价结果整体直评

### 8. `FinalEvaluationProjection`

用途：

- 生成对外正式结果对象前的最后投影层
- 属于后端内部过渡对象，不直接等同于最终对外 API 返回体

建议字段：

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
- `supportingDimensionMap`
- `overallConfidence`

说明：

- `supportingDimensionMap` 可作为内部追踪字段保存，不要求前端直接消费
- 对外 API 最终仍应返回正式输出 Schema 所要求的稳定对象

## 顶层输出字段映射原则

### `commercialValue`

主要来源：

- `marketAttraction`

次级来源：

- `characterMomentum`

约束来源：

- `fatalRisk`
- `InputScreeningResult`
- `ConsistencyCheckResult`

### `writingQuality`

主要来源：

- `narrativeExecution`

次级来源：

- `characterMomentum`

约束来源：

- `fatalRisk`
- `ConsistencyCheckResult`

### `innovationScore`

主要来源：

- `noveltyUtility`

约束来源：

- `fatalRisk`
- `ConsistencyCheckResult`

### `signingProbability`

主要来源：

- `commercialValue`
- `writingQuality`
- `innovationScore`

约束来源：

- `fatalRisk`
- `InputScreeningResult`
- `ConsistencyCheckResult`

说明：

- 当前阶段不在文档中硬编码固定权重公式
- 先固定“主要来源、次级来源、上限约束”三层关系
- 具体权重应在 Evals 校准后再冻结到正式实现中

## 错误与不可评语义

建议至少区分以下错误类别：

- `input_invalid`
- `input_unrateable`
- `rubric_evaluation_failed`
- `rubric_incomplete`
- `consistency_conflict`
- `aggregation_failed`
- `provider_failure`

原则：

- 不可评应走结构化错误或结构化任务状态，而不是伪造低分结果
- 结构失败与判断失败应明确区分
- 内部阶段失败原因应支持进入 Evals 报告

## 与 `packages/schemas/` 的关系

后续建议落地顺序：

1. 在 `packages/schemas/output/` 中优先冻结最终输出结构
2. 在 `packages/schemas/evals/` 中定义阶段评测与差异报告结构
3. 再按正式主线引入内部中间契约 Schema

这样做的原因：

- 先保证正式接口稳定
- 再扩展内部阶段结构
- 避免中间结构反过来绑死对外接口
