# API v0 总契约说明

## 作用域

`API v0` 是 `Phase 1` 本地单用户交付的正式 API 契约。

## Base Path

`/api`

## 正式路由

- `GET /api/provider-status`
- `POST /api/provider-status/runtime-key`
- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

## 通用 Envelope

### 成功

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": null
}
```

### 失败

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入参数不合法"
  },
  "meta": null
}
```

## `GET /api/provider-status`

返回当前真实 provider 的运行状态：

- `providerId`
- `modelId`
- `configured`
- `configurationSource`
- `canAnalyze`
- `canConfigureFromUi`

说明：

- `configurationSource` 当前只会是 `missing / startup_env / runtime_memory`
- 缺少 key 时 API 仍可只读启动，但 `canAnalyze=false`

## `POST /api/provider-status/runtime-key`

向当前 API 进程写入一次性 runtime key。

约束：

- 只允许本机访问
- 请求带转发头或来源不是回环地址时返回 `403 FORBIDDEN`
- 启动期已配置 key，或当前进程已录入过 runtime key 时返回 `409 PROVIDER_CONFIGURATION_LOCKED`
- 成功后 `configurationSource=runtime_memory`

## `POST /api/tasks`

### 提交模式

- `application/json`
- `multipart/form-data`

### multipart 固定字段

- `title`
- `sourceType`
- `chaptersFile`
- `outlineFile`

### JSON 核心字段

- `title`
- `chapters`
- `outline`
- `sourceType`

### 成功语义

- 返回 `201`
- 返回完整 `EvaluationTask`
- 初始状态为 `queued + not_available`
- 任务会在 API 进程内通过后台任务继续推进

### 前置约束

- 当前 provider 未配置时返回 `409 PROVIDER_NOT_CONFIGURED`
- 请求边界错误不创建任务

### 非幂等边界

- `POST /api/tasks` 明确定义为非幂等
- 每次成功创建都产生新的 `taskId`
- 不提供基于提交内容的自动去重

### 上传错误码

- `UNSUPPORTED_UPLOAD_FORMAT`
- `UPLOAD_TOO_LARGE`
- `UPLOAD_PARSE_FAILED`

## `GET /api/tasks/{taskId}`

返回：

- 任务详情
- 当前 `status / resultStatus`
- 错误码与错误消息
- `schemaVersion / promptVersion / rubricVersion / providerId / modelId`

约束：

- 历史失败、历史阻断和兼容降级后的任务都作为稳定资源返回 `200`
- `taskId` 不存在时返回 `404 TASK_NOT_FOUND`
- 若任务本身是 `completed + available`，但关联结果资源已经是旧 schema 或损坏 payload，读取时会标准化为 `completed + not_available`

## `GET /api/tasks/{taskId}/result`

返回 `EvaluationResultResource`：

- `available`：返回正式 `result`
- `blocked`：`result=null`，`message` 必填
- `not_available`：`result=null`，`message` 必填

约束：

- `blocked` 与 `not_available` 不返回伪结果
- 任务存在但结果不可读时仍返回 `200`
- 旧版持久化结果或损坏结果会按 `not_available` 返回，并携带兼容提示

## `GET /api/dashboard`

返回首页摘要：

- `recentTasks`
- `activeTasks`
- `recentResults`

说明：

- `recentResults` 只包含当前仍能按新结果 schema 正常读取的结果

## `GET /api/history`

### Query 参数

- `q`
- `status`
- `cursor`
- `limit`

### 正式语义

- `q`：标题子串搜索
- `status`：只支持任务状态枚举
- `cursor`：按 `createdAt desc, taskId desc` 的不透明游标
- `limit`：默认 `20`，最大 `50`

### 返回语义

- 只返回按任务组织的摘要列表
- 不返回完整正式结果正文
- `HistoryList.meta` 会同时复制到 Envelope 的 `meta`

## 关联真源

- 状态与错误：`apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 上传边界：`docs/contracts/file-upload-and-ingestion-boundary.md`
- 前端最小消费：`docs/contracts/frontend-minimal-api-assumptions.md`
