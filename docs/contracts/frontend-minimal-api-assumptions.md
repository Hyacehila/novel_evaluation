# 前端最小 API 假设契约

## 文档角色

本文档为前端提供应当对齐的 API 最小消费假设。它以正式契约与当前 API 实现为准。

## 路由集合

- `GET /api/provider-status`
- `POST /api/provider-status/runtime-key`
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

### `configurationSource`

- `missing`
- `startup_env`
- `runtime_memory`

### `novelType`

- `female_general`
- `fantasy_upgrade`
- `urban_reality`
- `history_military`
- `sci_fi_apocalypse`
- `suspense_horror`
- `game_derivative`
- `general_fallback`

## Provider 状态假设

- `GET /api/provider-status` 返回 provider 当前是否可分析
- `POST /api/provider-status/runtime-key` 仅在 `configurationSource=missing` 时可用
- runtime key 录入成功后，前端应把 provider 状态视为 `runtime_memory`
- runtime key 接口可能返回：
  - `FORBIDDEN`
  - `PROVIDER_CONFIGURATION_LOCKED`
  - `VALIDATION_ERROR`

## 创建任务假设

- 支持 JSON 与 multipart
- 创建成功返回完整 `EvaluationTask`
- 初始状态是 `queued + not_available`
- 新建任务的 `novelType / typeClassificationConfidence / typeFallbackUsed` 初始允许为 `null`
- `POST /api/tasks` 非幂等
- provider 未配置时返回 `409 PROVIDER_NOT_CONFIGURED`

## 任务读取假设

- 任务在 `processing` 中可能已经补齐类型识别字段
- `resultAvailable=true` 当且仅当 `resultStatus=available`
- 当前允许 `completed + not_available` 作为历史兼容状态

## 结果读取假设

- `available` 才返回 `result`
- `blocked/not_available` 均返回 `result=null`
- `result.overall.platformCandidates` 为结构化对象数组，而非字符串数组
- `result.typeAssessment` 允许为 `null`，用于兼容历史结果读取
- 前端本地可派生 `fetch_failed`，但它不属于后端正式枚举
- 旧版持久化结果或损坏结果会被 API 标准化为 `not_available`

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
- `PROVIDER_NOT_CONFIGURED`
- `PROVIDER_CONFIGURATION_LOCKED`
- `FORBIDDEN`
- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `INTERNAL_ERROR`
