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
- `completed + not_available`
- `failed + not_available`

约束：

- `resultAvailable=true` 当且仅当 `resultStatus=available`
- `completed + blocked` 必须携带阻断类 `errorCode + errorMessage`
- `failed + not_available` 必须携带失败类 `errorCode + errorMessage`
- `completed + not_available` 允许存在，但它不是正常成功路径；当前只用于读取阶段把“缺失/过期/损坏的结果资源”标准化为不可用
- 不允许 `queued/processing + available`
- 不允许 `failed + blocked`

## 状态迁移

正常主链：

```text
queued -> processing -> completed
queued -> processing -> failed
```

恢复路径：

- API 启动时会扫描遗留 `queued / processing` 任务
- 这些任务会在恢复阶段统一标记为 `failed + not_available`

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
- 结果资源固定返回 `message`，当前默认文案为“结果未满足正式展示条件”

## 技术失败

进入 `failed + not_available` 的典型错误码：

- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `INTERNAL_ERROR`
- `PROVIDER_NOT_CONFIGURED` 作为失败类错误码被保留，但当前用户主链通过 `POST /api/tasks` 前置检查直接返回 `409`，不会先创建任务再失败

补充：

- 进程重启后遗留任务会转入这一类技术失败
- 上游 provider 原始错误文案会在进入任务对象前被清洗

## 兼容降级

以下场景不会伪造成功结果，而会标准化为 `completed + not_available` 或 `resultStatus=not_available`：

- 持久化结果仍是旧版顶层字段结构
- 持久化结果 payload 已损坏
- 任务对象显示可用，但关联结果资源缺失

## 请求边界错误

这些错误不创建任务：

- `VALIDATION_ERROR`
- `EMPTY_SUBMISSION`
- `INVALID_SOURCE_TYPE`
- `UNSUPPORTED_UPLOAD_FORMAT`
- `UPLOAD_TOO_LARGE`
- `UPLOAD_PARSE_FAILED`
- `FORBIDDEN`
- `PROVIDER_CONFIGURATION_LOCKED`
- `PROVIDER_NOT_CONFIGURED`

## 资源错误

当前 API 明确发出的资源错误：

- `TASK_NOT_FOUND`

以下错误码保留在枚举中，但当前 API 路由未主动发出：

- `TASK_STATE_CONFLICT`
- `RESULT_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`

## HTTP 映射原则

### 创建任务

- `201`：创建成功
- `403`：runtime key 配置接口的本机访问限制不满足
- `409`：provider 未配置或配置已锁定
- `422`：请求边界错误，不创建任务

### 读取任务或结果

- `200`：资源读取成功，包括历史失败、历史阻断和兼容降级
- `404`：任务不存在
- `422`：history 查询参数不合法

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
