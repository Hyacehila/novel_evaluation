# 领域模型

## 文档角色

本文档冻结当前仓库在 `Phase 1` / `DevFleet-Ready` 阶段的共享领域对象语义。

它负责回答：

- 核心对象有哪些
- 每个对象的冻结字段是什么
- 哪些字段是派生字段
- 哪些约束属于对象自身不变量
- 对象之间如何关联

本文档与 `docs/contracts/canonical-schema-index.md` 共同构成当前文档阶段的对象真源：

- 本文负责解释对象本体、字段语义、关系和不变量
- `canonical-schema-index.md` 负责索引这些对象未来应落到 `packages/schemas/` 的哪个子域

本文档不负责：

- 定义 API 路径
- 定义前端 View Model
- 替代正式 schema 文件
- 定义 Prompt 正文

## 建模前提

- 当前项目定位为开源项目、本地部署、本机联调
- `Phase 1` 以本地单用户可用为前提，不把鉴权、多租户和工作区隔离作为进入 `DevFleet-Ready` 的阻塞项
- 当前不把 `ownerRef`、`userId`、`workspaceId`、`tenantId` 纳入正式冻结字段
- 正式评分主线固定为：输入预检查 → `LLM rubric` 分点评价 → 轻量一致性整理 → 新模型聚合输出 → 正式结果投影
- 对外结果结构保持稳定，对内阶段对象允许分层演进

## 共享词表与元信息

### 输入组成 `inputComposition`

冻结枚举：

- `chapters_outline`
- `chapters_only`
- `outline_only`

### 评估模式 `evaluationMode`

冻结枚举：

- `full`
- `degraded`

说明：

- `full` 只用于正文与大纲都存在且满足正式联合评估条件的场景
- `degraded` 用于单侧输入仍允许继续评估的场景

### 任务状态 `status`

冻结枚举：

- `queued`
- `processing`
- `completed`
- `failed`

### 结果状态 `resultStatus`

冻结枚举：

- `available`
- `not_available`
- `blocked`

### 版本元信息

以下元信息一旦进入对象，就必须保持统一语义：

- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`

## 对象关系图

```text
Manuscript -> JointSubmissionRequest -> EvaluationTask -> EvaluationResult
                                               |
                                               -> EvaluationTaskSummary

EvalCase -> EvalRecord -> EvalBaseline / EvalReport
```

说明：

- `Manuscript` 是联合投稿包的领域对象
- `JointSubmissionRequest` 是创建任务时使用的边界请求对象
- `EvaluationTask` 是执行状态和结果状态的主承载对象
- `EvaluationResult` 只在 `resultStatus=available` 时出现正式结果正文
- `EvalRecord` 用于记录一次评测执行及其与基线的关系

## 领域对象

### 1. 稿件 `Manuscript`

用途：

- 表示一次可进入正式评分主线的联合投稿包
- 为输入预检查、阶段契约和对外结果提供统一输入语义

冻结字段：

- `title`
- `chapters`
- `outline`
- `sourceType`
- `hasChapters`
- `hasOutline`
- `inputComposition`

字段语义：

- `title`：稿件标题或任务展示标题
- `chapters`：正文数组；每个元素至少包含 `content`，可选 `title`
- `outline`：大纲对象；当前最小冻结字段为 `content`
- `sourceType`：输入来源，冻结枚举：
  - `direct_input`
  - `file_upload`
  - `history_derived`
- `hasChapters`：是否存在可用正文输入
- `hasOutline`：是否存在可用大纲输入
- `inputComposition`：由输入组成派生出的正式词表

派生字段：

- `hasChapters`
- `hasOutline`
- `inputComposition`

不变量：

- `chapters` 与 `outline` 至少存在一侧
- `inputComposition` 不允许手工随意填写，必须由 `chapters` / `outline` 派生
- `chapters_outline` 只在两侧都存在时成立
- `chapters_only` 与 `outline_only` 只能二选一
- `sourceType` 只描述来源，不得反向决定评分模式

关系：

- `Manuscript` 是 `JointSubmissionRequest` 和 `EvaluationTask` 的上游输入语义来源
- `Manuscript` 不负责表达执行状态和结果状态

### 2. 创建请求 `JointSubmissionRequest`

用途：

- 表示 `POST /api/tasks` 的最小正式请求对象
- 作为 API、frontend adapter 与 application use case 的共同输入边界

冻结字段：

- `title`
- `chapters`
- `outline`
- `sourceType`

派生字段：

- `inputComposition`
- `hasChapters`
- `hasOutline`

不变量：

- 请求边界必须保证至少存在一侧输入
- 边界校验失败时，不创建 `EvaluationTask`
- `JointSubmissionRequest` 不携带任务状态、结果状态和评分结果字段

关系：

- 成功通过边界校验后，`JointSubmissionRequest` 转化为 `EvaluationTask` 的输入来源
- 该对象的字段语义必须与 `Manuscript` 保持一致

### 3. 评测任务 `EvaluationTask`

用途：

- 表示一次独立、可追踪的评分任务
- 是 API、worker、frontend、evals 共享的任务对象真源

冻结字段：

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
- `createdAt`
- `startedAt`
- `completedAt`
- `updatedAt`

字段语义：

- `taskId`：任务唯一标识
- `inputSummary`：面向任务页和摘要页的最小输入摘要
- `resultAvailable`：`resultStatus` 的派生布尔语义
- `errorCode` / `errorMessage`：任务失败或结果阻断时的结构化错误语义
- `startedAt`：任务正式开始执行时间，可为空
- `completedAt`：任务进入终态的时间，可为空

派生字段：

- `resultAvailable`

不变量：

- `taskId` 一旦创建不可变
- `resultAvailable=true` 当且仅当 `resultStatus=available`
- `queued` 与 `processing` 只能搭配 `resultStatus=not_available`
- `completed` 只能搭配：
  - `resultStatus=available`
  - `resultStatus=blocked`
- `failed` 只能搭配 `resultStatus=not_available`
- `errorCode` 在 `failed` 或 `blocked` 时必须存在
- `EvaluationTask` 是状态真源，前端不得自行发明第二套后端状态

关系：

- `EvaluationTask` 由 `JointSubmissionRequest` 创建
- `EvaluationTask` 成功完成后，可能生成 `EvaluationResult`
- `EvaluationTask` 的字段语义必须与 `apps/api/contracts/job-lifecycle-and-error-semantics.md` 保持一致

### 4. 任务摘要 `EvaluationTaskSummary`

用途：

- 为工作台首页、历史记录页和列表视图提供最小摘要对象

冻结字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `status`
- `createdAt`
- `resultAvailable`
- `resultStatus`

不变量：

- `EvaluationTaskSummary` 只承载摘要，不替代详情对象
- 它不得新增详情对象没有定义的正式状态语义

关系：

- `EvaluationTaskSummary` 是 `EvaluationTask` 的列表投影
- 它必须从 `EvaluationTask` 派生，而不是独立维护第二套语义

### 5. 正式结果 `EvaluationResult`

用途：

- 表示面向前端和外部消费的正式结果正文
- 只在任务进入正式可展示状态时出现

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

`detailedAnalysis` 当前冻结子字段：

- `plot`
- `character`
- `pacing`
- `worldBuilding`

不变量：

- `EvaluationResult` 只在 `EvaluationTask.resultStatus=available` 时存在正式结果正文
- 顶层四个评分字段必须是 `0-100` 的整数
- `platforms` 必须是 `PlatformRecommendation[]`
- `strengths` 与 `weaknesses` 必须是字符串数组
- `blocked` 或 `not_available` 场景不允许伪造 `EvaluationResult`

关系：

- `EvaluationResult` 由阶段对象经聚合与正式结果投影后生成
- 对外字段语义以 `docs/contracts/json-contracts.md` 为主说明文档

### 6. 平台推荐 `PlatformRecommendation`

用途：

- 表示作品与目标平台之间的匹配建议

冻结字段：

- `name`
- `percentage`
- `reason`

不变量：

- `percentage` 必须是 `0-100` 的整数
- `reason` 必须解释匹配原因，而不是只重复平台名称
- `PlatformRecommendation` 不承载平台运营策略字段

关系：

- `PlatformRecommendation` 只作为 `EvaluationResult.platforms` 的成员对象出现

### 7. 评测记录 `EvalRecord`

用途：

- 表示一次结构化评测执行与基线对比记录
- 为 Prompt、Schema、Provider / Model 变更提供最小回归追踪对象

冻结字段：

- `evalCaseId`
- `taskId`
- `inputComposition`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `taskStatus`
- `resultStatus`
- `contractValid`
- `baselineId`
- `reportId`
- `regressionConclusion`
- `startedAt`
- `finishedAt`
- `diffSummary`

字段语义：

- `contractValid`：结果是否通过正式结构校验
- `baselineId`：所比对的基线标识，可为空
- `reportId`：所属报告标识，可为空
- `regressionConclusion`：本次评测结论，如通过、退化、阻断、失败

不变量：

- `EvalRecord` 必须记录版本元信息
- `taskStatus` 与 `resultStatus` 必须沿用正式任务词表
- 结构失败与质量退化不能混写为同一结论

关系：

- `EvalRecord` 来源于 `EvalCase` 的一次运行
- `EvalRecord` 可被 `EvalBaseline` 和 `EvalReport` 汇总消费

## 固定词表对象

以下内容属于固定词表，不作为独立可变业务实体：

- 新 `8` 轴主评价层词表
- 旧四维骨架层词表
- `fatalRisk` 风险词表
- 任务状态与结果状态枚举

这些词表的语义应分别以：

- `docs/contracts/rubric-stage-contracts.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`

为准，不在实现阶段私自扩写。

## 当前待确认项

以下内容当前不进入冻结字段，但必须显式保留为待确认项：

- 多用户场景下是否需要 `ownerRef / userId / workspaceId / tenantId`
- `EvaluationResult` 是否需要额外公开内部追踪字段
- `EvalReport` 是否拆分为单次报告和比较报告两类正式结构

## 完成标准

满足以下条件时，可认为领域模型已冻结到足以支撑 DevFleet 文档 mission：

- 共享对象不再停留在“建议属性”层级
- 对象字段、派生字段和不变量已经可被 schema / application / API 共用
- 任务状态和结果状态有单一承载对象
- 多个 mission 不会再围绕对象边界各写一套解释
