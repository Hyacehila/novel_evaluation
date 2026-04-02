# 领域模型

## 文档角色

本文档冻结当前共享业务对象的语义、不变量和关系。

## 建模前提

- 当前只面向本地单用户交付
- 多用户字段移入未来扩展保留位，不作为当前阻塞项
- 用户任务由 API 进程内执行器推进
- 回归任务由 worker/evals 驱动

## 核心对象

### `Manuscript`

字段核心：

- `title`
- `chapters`
- `outline`
- `sourceType`
- `inputComposition`
- `hasChapters`
- `hasOutline`

不变量：

- `chapters` 与 `outline` 至少存在一侧
- `inputComposition` 必须由输入派生

### `JointSubmissionRequest`

字段核心：

- `title`
- `chapters`
- `outline`
- `sourceType`

说明：

- 对应 `POST /api/tasks`
- JSON 与 multipart 都映射到该对象

### `EvaluationTask`

字段核心：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `evaluationMode`
- `status`
- `resultStatus`
- `resultAvailable`
- `errorCode`
- `errorMessage`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `novelType`
- `typeClassificationConfidence`
- `typeFallbackUsed`
- `createdAt`
- `startedAt`
- `completedAt`
- `updatedAt`

不变量：

- 合法状态组合仅限：
  - `queued + not_available`
  - `processing + not_available`
  - `completed + available`
  - `completed + blocked`
  - `completed + not_available`
  - `failed + not_available`
- 类型相关字段允许在任务执行中从 `null` 逐步变为有效值

### `EvaluationResultResource`

字段核心：

- `taskId`
- `resultStatus`
- `resultTime`
- `result`
- `message`

说明：

- `resultStatus=available` 时才有正式 `result`
- `blocked` 与 `not_available` 不允许伪造 `result`

### `EvaluationResult`

字段核心：

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `resultTime`
- `axes`
- `overall`
- `typeAssessment`

说明：

- `axes` 必须完整覆盖全部 `8` 个 `AxisId`
- 每个轴包含 `scoreBand / score / summary / reason / degradedByInput / riskTags`
- `overall` 当前包含：
  - `score`
  - `verdict`
  - `verdictSubQuote`
  - `summary`
  - `platformCandidates`
  - `marketFit`
  - `strengths`
  - `weaknesses`
- `typeAssessment` 当前为可选，用于兼容历史结果读取

### `TypeClassificationResult`

字段核心：

- `candidates`
- `novelType`
- `classificationConfidence`
- `fallbackUsed`
- `summary`

说明：

- `candidates` 固定为 `Top-3`
- `novelType` 由后端阈值逻辑最终选择

### `TypeLensEvaluationResult`

字段核心：

- `novelType`
- `summary`
- `items`
- `overallConfidence`

说明：

- `items` 必须完整覆盖当前 `novelType` 对应的 `4` 个 lens

### `EvalRecord`

字段核心：

- `evalCaseId`
- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `taskStatus`
- `resultStatus`
- `errorCode`
- `durationMs`

说明：

- 执行追踪信息进入 `EvalRecord` 和日志
- 不进入 `FinalEvaluationProjection`

## 未来扩展保留位

以下字段明确保留到后续阶段，而非当前阻塞项：

- `ownerRef`
- `userId`
- `workspaceId`
- `tenantId`
