# API v0 总契约说明

## 作用域

`API v0` 是 `Phase 1` 本地单用户交付的正式 API 契约。

## Base Path

`/api`

## 正式路由

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
- 返回最小 `EvaluationTask`
- 初始状态为 `queued + not_available`

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
- 状态与结果状态
- 错误码与错误消息

约束：

- 历史失败与阻断都应作为稳定资源返回 `200`
- `taskId` 不存在时返回 `404`

## `GET /api/tasks/{taskId}/result`

返回 `EvaluationResultResource`：

- `available`：返回正式 `result`
- `blocked`：`result=null`
- `not_available`：`result=null`

约束：

- `blocked` 与 `not_available` 不返回伪结果
- 任务存在但结果不可读时仍返回 `200`

## `GET /api/dashboard`

返回首页摘要：

- `recentTasks`
- `activeTasks`
- `recentResults`

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

## 关联真源

- 状态与错误：`apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 上传边界：`docs/contracts/file-upload-and-ingestion-boundary.md`
- 前端最小消费：`docs/contracts/frontend-minimal-api-assumptions.md`
