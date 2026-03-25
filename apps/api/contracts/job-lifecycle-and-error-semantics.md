# 任务生命周期与错误语义说明

## 文档角色

本文档冻结 `API v0`、`packages/application/`、`apps/worker/`、前端轮询逻辑和 `evals/` 共用的：

- 任务状态枚举
- 结果状态枚举
- 合法状态组合
- 失败与阻断边界
- 错误码分类与 HTTP 映射原则

本文档不定义 API 路径本身；路径语义见 `apps/api/contracts/api-v0-overview.md`。

## 核心原则

- `status` 与 `resultStatus` 必须分离
- `EvaluationTask` 是状态语义的唯一主承载对象
- 不允许用伪成功结果掩盖失败或阻断
- 已持久化的任务失败/阻断，在读取时应表现为稳定资源状态，而不是新的接口异常
- 对外可见错误与内部诊断错误必须分层

## 任务对象最小状态字段

`EvaluationTask` 至少需要表达：

- `taskId`
- `status`
- `resultStatus`
- `resultAvailable`
- `errorCode`
- `errorMessage`
- `createdAt`
- `startedAt`
- `completedAt`
- `updatedAt`

说明：

- `resultAvailable` 是 `resultStatus` 的派生布尔值
- `errorCode` / `errorMessage` 用于表达失败或阻断原因
- 这些字段语义必须与 `docs/architecture/domain-model.md` 保持一致

## 任务状态 `status`

冻结枚举：

- `queued`
- `processing`
- `completed`
- `failed`

### `queued`

含义：

- 任务已创建
- 尚未开始正式执行
- 或正在等待执行资源

### `processing`

含义：

- 任务已进入正式执行链路
- 正在运行输入预检查、分点评价、一致性整理、聚合或投影中的某一步

### `completed`

含义：

- 任务执行链路已正常结束
- 不代表一定产出可展示正式结果正文

### `failed`

含义：

- 任务未能形成正常结束结论
- 原因属于技术失败、依赖失败、契约失败或执行链路崩溃

## 结果状态 `resultStatus`

冻结枚举：

- `available`
- `not_available`
- `blocked`

### `available`

含义：

- 存在可供前端正式展示的结果正文

### `not_available`

含义：

- 当前不存在可展示正式结果正文
- 任务仍可能处于执行中，或已经技术失败

### `blocked`

含义：

- 任务已正常结束，但因业务语义原因不允许展示正式结果正文
- 典型原因包括：联合输入不可评、严重跨输入冲突、结果不满足正式展示条件

## 状态转移规则

统一状态迁移：

```text
queued -> processing
queued -> failed
processing -> completed
processing -> failed
```

约束：

- 不允许 `completed -> processing`
- 不允许 `failed -> processing`
- 终态只能是 `completed` 或 `failed`

## 合法状态组合

当前正式允许以下组合：

| `status` | `resultStatus` | 含义 |
| --- | --- | --- |
| `queued` | `not_available` | 已创建，未开始执行 |
| `processing` | `not_available` | 执行中 |
| `completed` | `available` | 正常完成且结果可展示 |
| `completed` | `blocked` | 正常完成但结果被业务语义阻断 |
| `failed` | `not_available` | 技术失败或执行失败 |

补充约束：

- `resultAvailable=true` 当且仅当 `resultStatus=available`
- `completed + blocked` 必须携带阻断类 `errorCode`
- `failed + not_available` 必须携带失败类 `errorCode`
- 不允许 `failed + blocked`
- 不允许 `queued/processing + available`

## 失败与阻断边界

### 一、请求边界错误：不创建任务

以下情况属于请求边界错误：

- 请求体结构非法
- 必填字段缺失
- `sourceType` 非法
- 提交内容为空

处理原则：

- 返回错误 envelope
- 不创建 `EvaluationTask`
- HTTP 状态码通常为 `400` 或 `422`

### 二、业务阻断：`completed + blocked`

以下情况属于业务阻断：

- `JOINT_INPUT_UNRATEABLE`
- `INSUFFICIENT_CHAPTERS_INPUT`
- `INSUFFICIENT_OUTLINE_INPUT`
- `JOINT_INPUT_MISMATCH`
- `RESULT_BLOCKED`

处理原则：

- 任务链路正常结束
- 结果正文不生成
- `EvaluationTask` 进入 `completed + blocked`
- `GET /api/tasks/{taskId}` 与 `GET /api/tasks/{taskId}/result` 返回 `200`，由对象状态表达阻断语义

### 三、技术失败：`failed + not_available`

以下情况属于技术失败：

- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `INTERNAL_ERROR`

处理原则：

- 任务未形成正常结束结论
- `EvaluationTask` 进入 `failed + not_available`
- 后续读取该任务时应返回稳定任务状态，而不是把历史失败重新包装成新的 `5xx`

## 错误码分层

### 1. 请求边界错误

冻结最小集合：

- `VALIDATION_ERROR`
- `EMPTY_SUBMISSION`
- `INVALID_SOURCE_TYPE`

### 2. 联合输入与业务阻断错误

冻结最小集合：

- `JOINT_INPUT_UNRATEABLE`
- `INSUFFICIENT_CHAPTERS_INPUT`
- `INSUFFICIENT_OUTLINE_INPUT`
- `JOINT_INPUT_MISMATCH`
- `RESULT_BLOCKED`

### 3. 任务与资源错误

冻结最小集合：

- `TASK_NOT_FOUND`
- `TASK_STATE_CONFLICT`
- `RESULT_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`

### 4. 契约与执行失败错误

冻结最小集合：

- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

## HTTP 状态码映射原则

### 创建任务 `POST /api/tasks`

- `201`：任务创建成功
- `400` / `422`：请求边界错误，不创建任务
- `409`：状态冲突或幂等冲突
- `502` / `503`：当前请求依赖不可用且未形成任务
- `500`：当前请求处理失败且未形成任务

### 读取任务与读取结果

- `200`：资源读取成功，包括：
  - 任务执行中
  - 任务已完成且结果可用
  - 任务已完成但结果被阻断
  - 任务已失败且失败状态已被持久化
- `404`：`taskId` 或结果资源不存在
- `500` / `502` / `503`：当前读取请求本身失败，而不是历史任务失败

## 用户可见错误与内部诊断错误

### 用户可见错误

对外最小字段：

- `code`
- `message`

要求：

- 可被前端稳定映射
- 不泄露内部 SDK、堆栈、密钥或原始敏感输出

### 内部诊断错误

内部可额外记录：

- 原始异常摘要
- Provider 响应摘要
- `requestId`
- 重试次数
- `inputComposition`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`

## 前端与 Evals 必须遵守的规则

- 前端不得把 `fetch_failed` 反向写回后端任务枚举
- `evals/` 必须区分业务阻断与技术失败
- 结果页只有在 `resultStatus=available` 时进入正式正文态
- `blocked` 与 `failed` 都不能伪装成“低分但可看”的结果正文

## 完成标准

满足以下条件时，可认为状态与错误语义已足以支撑 DevFleet 后续开发：

- API、frontend、worker、evals 对状态组合理解一致
- 请求边界错误、业务阻断和技术失败有稳定分层
- 已持久化的失败/阻断在读取时不再引发语义漂移
- 不会再通过伪结果掩盖阻断或失败
