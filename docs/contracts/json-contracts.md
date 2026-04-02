# JSON 契约说明

## 文档角色

本文档冻结当前阶段与正式结构输出最相关的对象语义，用于回答：

- 哪些对象属于当前正式 JSON 契约范围
- 当前对外正式结果对象长什么样
- 阻断与失败场景如何与结果正文分离
- 内部阶段对象如何收束到对外结果对象

本文档不替代正式 schema 文件；它负责解释字段语义、层次关系和治理约束。

## 真源关系

当前结构真源优先级为：

1. `packages/schemas/` 中已落地的正式 schema 文件
2. `docs/contracts/canonical-schema-index.md`
3. 本文档
4. `docs/contracts/rubric-stage-contracts.md`
5. API / 前端 / Evals 消费文档

## 当前正式 JSON 契约对象

本文档当前解释以下对象：

- `JointSubmissionRequest`
- `RuntimeProviderKeyRequest`
- `ProviderStatus`
- `EvaluationTask`
- `EvaluationResultResource`
- `EvaluationResult`
- `DashboardSummary`
- `HistoryList`
- `SuccessEnvelope / ErrorEnvelope`
- `FinalEvaluationProjection`（内部最后投影层）

## 统一原则

- 模型输出必须是严格 JSON
- 不允许在 JSON 外附带额外自然语言
- 不允许返回缺失核心字段的半结构化结果
- `blocked` 与 `not_available` 不允许伪造正式结果正文
- 对外结构稳定优先于内部阶段结构便利

## 一、创建请求对象 `JointSubmissionRequest`

最小字段：

- `title`
- `chapters`
- `outline`
- `sourceType`

约束：

- `chapters` 与 `outline` 至少存在一侧
- `sourceType` 当前冻结枚举：
  - `direct_input`
  - `file_upload`
  - `history_derived`

## 二、运行时 Provider 配置对象

### `RuntimeProviderKeyRequest`

最小字段：

- `apiKey`

约束：

- 必须是非空字符串
- 长度上限 `4096`

### `ProviderStatus`

最小字段：

- `providerId`
- `modelId`
- `configured`
- `configurationSource`
- `canAnalyze`
- `canConfigureFromUi`

## 三、任务对象 `EvaluationTask`

最小字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `hasChapters`
- `hasOutline`
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

约束：

- `inputComposition` 当前冻结枚举：
  - `chapters_outline`
  - `chapters_only`
  - `outline_only`
- `evaluationMode` 当前冻结枚举：
  - `full`
  - `degraded`
- `resultAvailable=true` 当且仅当 `resultStatus=available`
- 合法状态组合必须服从 `packages/schemas/output/task.py`
- 当前允许 `completed + not_available`，仅用于读取期兼容降级
- `novelType / typeClassificationConfidence / typeFallbackUsed` 当前允许为 `null`，因为类型识别会在执行中途写回

## 四、结果资源对象 `EvaluationResultResource`

最小字段：

- `taskId`
- `resultStatus`
- `resultTime`
- `result`
- `message`

约束：

- `available` 时必须有 `result` 与 `resultTime`
- `blocked / not_available` 时必须 `result=null`
- `blocked / not_available` 时必须有 `message`

## 五、正式结果对象 `EvaluationResult`

### 顶层字段

冻结字段：

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

### `axes`

`axes` 必须完整且唯一覆盖全部 `8` 个 `AxisId`：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

每个轴对象固定字段：

- `axisId`
- `scoreBand`
- `score`
- `summary`
- `reason`
- `degradedByInput`
- `riskTags`

### `overall`

当前冻结字段：

- `score`
- `verdict`
- `verdictSubQuote`
- `summary`
- `platformCandidates`
- `marketFit`
- `strengths`
- `weaknesses`

其中 `platformCandidates` 为对象数组，每个候选包含：

- `name`
- `weight`
- `pitchQuote`

并满足：

- 多个平台候选的 `weight` 之和必须为 `100`

### `typeAssessment`

当前保持可选，以兼容历史结果读取。存在时固定包含：

- `novelType`
- `classificationConfidence`
- `fallbackUsed`
- `summary`
- `lenses`

其中 `lenses` 必须完整覆盖当前类型固定的 `4` 个 lens，每个 lens 固定包含：

- `lensId`
- `label`
- `scoreBand`
- `reason`
- `evidenceRefs`
- `confidence`
- `degradedByInput`
- `riskTags`

### 结构约束

- `overall.score` 必须是 `0-100` 的整数
- `axes` 必须覆盖全部 `8` 轴
- `typeAssessment` 若存在，其 `lenses` 必须与当前 `novelType` 的固定 lens 集合完全一致
- 仅在 `resultStatus=available` 时返回 `EvaluationResult` 正文

### 兼容约束

以下旧字段不再是当前正式契约：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`
- `detailedAnalysis`

读取历史旧结果时：

- 若仍满足当前 `EvaluationResult` schema，可继续读取
- 若不满足当前 schema，则会降级为 `not_available`

## 六、摘要对象

### `DashboardSummary`

固定字段：

- `recentTasks`
- `activeTasks`
- `recentResults`

### `HistoryList`

固定字段：

- `items`
- `meta`

说明：

- `recentResults` 只包含当前仍能正常读取的新结果
- `HistoryList` 只返回任务摘要，不返回正式结果正文

## 七、Envelope 与错误对象

### `SuccessEnvelope`

最小结构：

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": null
}
```

### `ErrorEnvelope`

最小结构：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务暂时不可用"
  },
  "meta": null
}
```

### `ErrorObject`

最小字段：

- `code`
- `message`

可选字段：

- `details`
- `fieldErrors`
- `retryable`

约束：

- `message` 面向用户可读
- 不泄露内部堆栈、密钥或原始模型响应

## 八、对内阶段对象与对外结果的关系

当前内部结构固定为：

1. `InputScreeningResult`
2. `TypeClassificationResult`
3. `RubricEvaluationSet`
4. `TypeLensEvaluationResult`
5. `ConsistencyCheckResult`
6. `AggregatedRubricResult`
7. `FinalEvaluationProjection`
8. `EvaluationResult`

说明：

- `FinalEvaluationProjection` 是生成 `EvaluationResult` 前的内部最后一步，不直接暴露为正式 API DTO
- `AggregatedRubricResult` 只保留聚合草案字段，不再承载旧四维骨架输出

## 九、字段级治理要求

以下字段一旦被对象使用，就必须保持统一语义：

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
- `novelType`
- `typeClassificationConfidence`
- `typeFallbackUsed`

若变更这些字段，必须同步检查：

- `docs/contracts/canonical-schema-index.md`
- `docs/contracts/rubric-stage-contracts.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `apps/web/src/api/contracts.ts`
