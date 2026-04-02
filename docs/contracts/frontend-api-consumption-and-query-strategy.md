# 前端 API 消费与查询策略

## 核心结论

- 服务端状态统一使用 `TanStack Query`
- 创建任务使用 Mutation
- 任务状态继续采用 `Polling-First`
- 页面只消费 adapter 输出的 View Model
- provider 状态单独查询
- 历史页使用 `q/status/cursor/limit`

## Query Key 建议

- `dashboard-summary`
- `provider-status`
- `task-detail:{taskId}`
- `task-result:{taskId}`
- `history-list:{q}:{status}:{cursor}:{limit}`

## 页面策略

### 首页

- 首次进入立即读取 `dashboard`
- 存在 `queued/processing` 任务时每 `15s` 轮询

### Provider 状态

- 新建任务页首次进入读取 `provider-status`
- 当前实现不为 `provider-status` 配置定时轮询
- runtime key 录入成功后，失效 `provider-status`、`dashboard-summary`、`history-list:*`

### 输入页

- `createTask` 使用 Mutation
- 支持 JSON 与 multipart 两条提交路径
- 提交前先检查 `provider-status.canAnalyze`
- 提交成功后失效 `dashboard-summary` 与 `history-list:*`

### 任务页

- `queued/processing` 时每 `2s` 轮询
- 任务终态后停止轮询
- 任务页固定读取并展示类型识别区域
- `processing` 中若后端已写回 `novelType`，页面应立即显示类型 badge、置信度和兜底标记
- `completed + available` 展示结果入口
- `completed + blocked`、`completed + not_available` 与 `failed + not_available` 展示语义态

### 结果页

- 先读取 `taskDetail(taskId)`
- 仅当任务不是 `queued/processing` 时才启用 `taskResult(taskId)`
- `available` 时展示：
  - 总体判断
  - 类型评价模块（若 `typeAssessment` 存在）
  - `8` 轴 rubric 结果
- `blocked/not_available` 进入语义态，不展示正文
- 网络失败可本地派生 `fetch_failed`

### 历史页

- 搜索词与状态进入 URL
- `q` 建议 `400ms` 防抖
- 首期不轮询
- 使用游标分页优先

## Adapter 规则

前端请求层拆为：

1. HTTP client
2. endpoint
3. mapper

页面不得直接处理 envelope、错误码和 DTO 细节。

## 失效策略

- 创建任务成功：失效 `dashboard-summary`、`history-list:*`
- 创建任务成功：同时可把返回的 `EvaluationTask` 写入 `task-detail:{taskId}` 缓存
- runtime key 录入成功：失效 `provider-status`、`dashboard-summary`、`history-list:*`
- 手动刷新历史：仅重取当前 `history-list:*`
