# JSON 契约说明

## 文档角色

本文档冻结当前阶段与正式结构输出最相关的对象语义，用于回答：

- 哪些对象属于当前正式 JSON 契约范围
- 对外正式结果对象包含哪些字段
- 阻断与失败场景如何与结果正文分离
- 结果字段与内部 `rubric` 主线之间是什么关系

本文档不替代正式 schema 文件；它负责解释字段语义、层次关系和治理约束。

## 真源关系

当前阶段的结构真源优先级为：

1. `packages/schemas/` 中已落地的正式 schema 文件
2. `docs/contracts/canonical-schema-index.md`
3. 本文档 `JSON 契约说明`
4. `docs/contracts/rubric-stage-contracts.md`
5. API / 前端 / Evals 消费文档

约束：

- API DTO、前端假契约和 Evals 报告都不得反向定义第二套正式结果结构
- `Pydantic` 只负责边界表达与运行时校验，不替代正式 schema 真源

## 当前正式 JSON 契约对象

本文档当前解释以下对象：

- `JointSubmissionRequest`
- `EvaluationTask`
- `EvaluationResult`
- `PlatformRecommendation`
- `ErrorEnvelope`
- `ErrorObject`
- `FinalEvaluationProjection`（后端内部最后投影层）

说明：

- `JointSubmissionRequest` 与 `EvaluationTask` 在 API 中直接可见
- `EvaluationResult` 是对外正式结果正文
- `FinalEvaluationProjection` 是生成 `EvaluationResult` 前的内部最后一步，不直接暴露为正式 API DTO

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
- 创建请求对象不携带任务状态、结果状态与评分结果字段

## 二、任务对象 `EvaluationTask`

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
- 合法状态组合必须服从 `apps/api/contracts/job-lifecycle-and-error-semantics.md`

## 三、正式结果对象 `EvaluationResult`

### 顶层字段

冻结字段：

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `resultTime`
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

### `detailedAnalysis`

当前冻结子字段：

- `plot`
- `character`
- `pacing`
- `worldBuilding`

### 结构约束

- 顶层四个评分字段必须是 `0-100` 的整数
- `strengths` 与 `weaknesses` 必须是字符串数组
- `platforms` 必须是 `PlatformRecommendation[]`
- `detailedAnalysis` 必须是对象，不允许退化为长文本 blob
- 仅在 `resultStatus=available` 时返回 `EvaluationResult` 正文

## 四、平台推荐对象 `PlatformRecommendation`

冻结字段：

- `name`
- `percentage`
- `reason`

约束：

- `percentage` 必须是 `0-100` 的整数
- `reason` 解释匹配原因，不是标签堆砌

## 五、错误 Envelope `ErrorEnvelope`

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

约束：

- `success=false` 时，`data` 必须为 `null`
- `error` 必须存在
- `meta` 可为空

## 六、错误对象 `ErrorObject`

最小字段：

- `code`
- `message`

可选字段：

- `details`
- `fieldErrors`
- `retryable`

约束：

- `code` 采用稳定错误码
- `message` 面向用户可读
- 不泄露内部堆栈、密钥或原始模型响应

## 七、对内阶段对象与对外结果的关系

### 内部三层

当前内部结构固定为：

1. 新 `8` 轴主评价层
2. 旧四维骨架层
3. 对外四分投影层

并保留 `fatalRisk` 作为跨层约束维度。

### 新 `8` 轴主评价层

固定词表：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

### 旧四维骨架层

固定词表：

- `marketAttraction`
- `narrativeExecution`
- `characterMomentum`
- `noveltyUtility`

### 对外字段映射方向

- `commercialValue`：主要来自 `marketAttraction`，并次级参考 `characterMomentum`
- `writingQuality`：主要来自 `narrativeExecution`，并次级参考 `characterMomentum`
- `innovationScore`：主要来自 `noveltyUtility`
- `signingProbability`：建立在前三项基础分之上，并受 `platformFit`、`fatalRisk`、输入预检查结果与一致性整理结果共同约束
- `strengths` / `weaknesses`：来自分点评价和聚合总结，不凭空生成
- `marketFit` / `editorVerdict` / `detailedAnalysis.*`：来自聚合与投影层，不是独立于评分过程的附属文案

## 八、阻断与失败语义

- `available`：返回正式结果正文
- `blocked`：任务正常结束，但结果正文不允许展示
- `not_available`：当前没有正式结果正文

约束：

- `blocked` 与 `not_available` 都不允许返回伪 `EvaluationResult`
- 技术失败与业务阻断必须分层，不允许混写成“低分但可读”结果

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

若变更这些字段，必须同步检查：

- `docs/contracts/schema-versioning-policy.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `evals/README.md`

## 完成标准

满足以下条件时，可认为 JSON 契约说明足以支撑 DevFleet 后续开发：

- 对外正式对象边界清晰
- 内部阶段对象与对外结果对象关系清楚
- 阻断和失败场景不再伪装为正式结果正文
- API、前端、Evals 不再围绕结果字段重复定义第二套语义
