# 前端 API 消费与查询策略

## 核心结论

- 服务端状态统一使用 `TanStack Query`
- 创建任务使用 Mutation
- 任务状态继续采用 `Polling-First`
- 页面只消费 adapter 输出的 View Model
- 历史页使用 `q/status/cursor/limit`

## Query Key 建议

- `dashboard-summary`
- `task-detail:{taskId}`
- `task-result:{taskId}`
- `history-list:{q}:{status}:{cursor}:{limit}`

## 页面策略

### 首页

- 首次进入立即读取 `dashboard`
- 存在 `queued/processing` 任务时可每 `15s` 轮询

### 输入页

- `createTask` 使用 Mutation
- 支持 JSON 与 multipart 两条提交路径
- 提交成功后失效 `dashboard-summary` 与 `history-list:*`

### 任务页

- `queued/processing` 时每 `5s` 轮询
- 任务终态后停止轮询
- `completed + available` 展示结果入口
- `completed + blocked` 与 `failed + not_available` 展示语义态

### 结果页

- 进入页面后读取 `taskResult(taskId)`
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
- 任务完成：失效 `dashboard-summary`、`history-list:*`、`task-result:{taskId}`
- 手动刷新历史：仅失效当前 `history-list:*`
