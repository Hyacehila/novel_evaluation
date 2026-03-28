# 前端页面数据视图模型

## 文档目的

本文定义前端实际导出的页面视图模型，用于在后端 DTO 与页面组件之间建立稳定的中间层。

本文不替代正式 Schema，也不要求后端直接按本文的模型原样返回。前端会先读取 DTO，再映射到这里的 View Model。

## 当前导出模型

当前 `apps/web/src/view-models/index.ts` 实际导出：

- `DashboardTaskSummaryView`
- `DashboardResultSummaryView`
- `DashboardSummaryView`
- `TaskDetailView`
- `AxisResultView`
- `OverallResultView`
- `ResultBodyView`
- `ResultDetailView`
- `HistoryListView`
- `ProviderStatusView`

说明：

- 历史页没有单独的 `HistoryTaskItemView`，而是复用 `DashboardTaskSummaryView`
- 新建任务页没有共享导出的 `InputDraftView`，而是使用本地 `deriveDraftSemantics()` 计算 `inputComposition / evaluationMode`

## 1. `DashboardTaskSummaryView`

工作台首页和历史页共用的任务摘要对象。

字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `status`
- `resultStatus`
- `createdAt`
- `resultAvailable`

## 2. `DashboardResultSummaryView`

工作台首页最近结果卡片对象。

字段：

- `taskId`
- `title`
- `resultTime`
- `overallScore`
- `overallVerdict`

## 3. `DashboardSummaryView`

工作台首页聚合对象。

字段：

- `recentTasks: DashboardTaskSummaryView[]`
- `activeTasks: DashboardTaskSummaryView[]`
- `recentResults: DashboardResultSummaryView[]`

## 4. `TaskDetailView`

任务详情页对象。

字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `hasChapters`
- `hasOutline`
- `evaluationMode`
- `status`
- `resultStatus`
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
- `resultAvailable`

## 5. 结果页对象

### `AxisResultView`

- `axisId`
- `scoreBand`
- `score`
- `summary`
- `reason`
- `degradedByInput`
- `riskTags`

### `OverallResultView`

- `score`
- `verdict`
- `summary`
- `platformCandidates`
- `marketFit`

### `ResultBodyView`

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `resultTime`
- `axes`
- `overall`

### `ResultDetailView`

- `taskId`
- `state`
- `resultStatus`
- `resultTime`
- `result`
- `message`

说明：

- `state` 当前与 `resultStatus` 保持同值，取值为 `available / blocked / not_available`
- `result=null` 时页面只能展示语义态，不展示正文

## 6. `HistoryListView`

字段：

- `items: DashboardTaskSummaryView[]`
- `meta.nextCursor`
- `meta.limit`

## 7. `ProviderStatusView`

字段：

- `providerId`
- `modelId`
- `configured`
- `configurationSource`
- `canAnalyze`
- `canConfigureFromUi`
- `statusLabel`
- `sourceLabel`
- `blockingMessage`

## 与正式契约的映射原则

- 结果页字段围绕 `EvaluationResultResourceDto -> ResultDetailView` 映射
- 当前正式结果核心语义是 `overall + axes`，前端不得再映射回旧的四项评分结构
- 历史页和工作台摘要可以生成展示型字段，但不得改变正式结果含义

## 与其他文档的关系

- 前后端职责边界见 `docs/contracts/frontend-backend-boundary.md`
- 前端最小 API 假设见 `docs/contracts/frontend-minimal-api-assumptions.md`
