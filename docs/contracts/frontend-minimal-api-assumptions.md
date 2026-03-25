# 前端最小 API 假设契约

## 文档角色

本文档为前端提供应当对齐的 `Phase 1` API 最小消费假设。它以正式契约为准，而不是以当前未完成实现为准。

## 路由集合

- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

## 必须识别的枚举

### `inputComposition`

- `chapters_outline`
- `chapters_only`
- `outline_only`

### `evaluationMode`

- `full`
- `degraded`

### `status`

- `queued`
- `processing`
- `completed`
- `failed`

### `resultStatus`

- `available`
- `not_available`
- `blocked`

## 创建任务假设

- 支持 JSON 与 multipart
- 创建成功返回完整 `EvaluationTask`
- 初始状态是 `queued + not_available`
- `POST /api/tasks` 非幂等

## 历史查询假设

- `q`：标题子串搜索
- `status`：任务状态筛选
- `cursor`：不透明游标
- `limit`：默认 `20`，最大 `50`

## 结果读取假设

- `available` 才返回 `result`
- `blocked/not_available` 均返回 `result=null`
- 前端本地可派生 `fetch_failed`，但它不属于后端正式枚举

## 前端必须识别的错误码

- `VALIDATION_ERROR`
- `EMPTY_SUBMISSION`
- `INVALID_SOURCE_TYPE`
- `UNSUPPORTED_UPLOAD_FORMAT`
- `UPLOAD_TOO_LARGE`
- `UPLOAD_PARSE_FAILED`
- `JOINT_INPUT_UNRATEABLE`
- `INSUFFICIENT_CHAPTERS_INPUT`
- `INSUFFICIENT_OUTLINE_INPUT`
- `JOINT_INPUT_MISMATCH`
- `RESULT_BLOCKED`
- `TASK_NOT_FOUND`
- `RESULT_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`
- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `INTERNAL_ERROR`
