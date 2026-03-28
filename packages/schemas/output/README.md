# `packages/schemas/output`

## 子域角色

该子域用于放置正式输出相关 schema。

## 当前正式对象

当前已经实际落地：

- `packages/schemas/output/task.py`
  - `EvaluationTask`
  - `EvaluationTaskSummary`
  - `RecentResultSummary`
- `packages/schemas/output/dashboard.py`
  - `DashboardSummary`
  - `HistoryList`
- `packages/schemas/output/provider_status.py`
  - `ProviderStatus`
- `packages/schemas/output/result.py`
  - `AxisEvaluationResult`
  - `OverallEvaluationResult`
  - `FinalEvaluationProjection`
  - `EvaluationResult`
  - `EvaluationResultResource`
- `packages/schemas/output/error.py`
  - `ErrorObject`
  - 阻断类 / 失败类错误码集合
- `packages/schemas/output/envelope.py`
  - `SuccessEnvelope`
  - `ErrorEnvelope`

## 作用边界

- 冻结任务对象与结果对象结构
- 冻结错误对象与 envelope 结构
- 冻结正式结果正文字段
- 不在本子域定义前端页面 View Model

## 当前边界说明

- `FinalEvaluationProjection` 与 `EvaluationResult` 当前共置于 `result.py`
- `EvaluationResult` 当前固定为 `overall + axes`
- `EvaluationResultResource` 是结果资源对象，不允许在 `blocked / not_available` 时返回伪结果正文
- `DashboardSummary` 与 `HistoryList` 属于摘要聚合对象，不反向成为领域对象真源

## 不负责

- 定义 API 路径
- 定义页面状态机
- 定义 Prompt 生命周期

## 验收方式

- `git diff --check`
- `rg "EvaluationTask|EvaluationTaskSummary|RecentResultSummary|DashboardSummary|HistoryList|EvaluationResultResource|ErrorEnvelope|ErrorObject|FinalEvaluationProjection" docs/contracts/canonical-schema-index.md packages/schemas/output/README.md`
