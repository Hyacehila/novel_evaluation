# 任务生命周期与错误语义说明

## 状态枚举

### `status`

- `queued`
- `processing`
- `completed`
- `failed`

### `resultStatus`

- `available`
- `not_available`
- `blocked`

## 合法状态组合

- `queued + not_available`
- `processing + not_available`
- `completed + available`
- `completed + blocked`
- `failed + not_available`

约束：

- `resultAvailable=true` 当且仅当 `resultStatus=available`
- `blocked` 与 `failed` 都必须携带结构化错误码
- 不允许 `failed + blocked`
- 不允许 `queued/processing + available`

## 状态迁移

```text
queued -> processing
queued -> failed
processing -> completed
processing -> failed
```

终态只有：

- `completed`
- `failed`

## 业务阻断

进入 `completed + blocked` 的典型错误码：

- `JOINT_INPUT_UNRATEABLE`
- `INSUFFICIENT_CHAPTERS_INPUT`
- `INSUFFICIENT_OUTLINE_INPUT`
- `JOINT_INPUT_MISMATCH`
- `RESULT_BLOCKED`

规则：

- 阻断是业务结论，不是技术失败
- 结果接口返回 `200`
- 不返回伪结果

## 技术失败

进入 `failed + not_available` 的典型错误码：

- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `INTERNAL_ERROR`

补充：

- 进程重启后遗留 `processing` 任务也转入这一类技术失败

## 请求边界错误

这些错误不创建任务：

- `VALIDATION_ERROR`
- `EMPTY_SUBMISSION`
- `INVALID_SOURCE_TYPE`
- `UNSUPPORTED_UPLOAD_FORMAT`
- `UPLOAD_TOO_LARGE`
- `UPLOAD_PARSE_FAILED`

## 资源错误

- `TASK_NOT_FOUND`
- `TASK_STATE_CONFLICT`
- `RESULT_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`

## HTTP 映射原则

### 创建任务

- `201`：创建成功
- `400/422`：请求边界错误，不创建任务
- `500/502/503`：当前请求本身失败且未形成任务

### 读取任务或结果

- `200`：资源读取成功，包括历史失败与阻断
- `404`：资源不存在
- `500/502/503`：读取请求自身失败

## 用户可见与诊断字段分层

### 用户可见

- `code`
- `message`

### 内部诊断至少记录

- `requestId`
- `taskId`
- `stage`
- `promptId`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `errorCode`
- `durationMs`
