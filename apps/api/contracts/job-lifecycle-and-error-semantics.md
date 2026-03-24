# 任务生命周期与错误语义说明

## 文档目的

本文档定义评测任务在 `API v0` 与后端实现中的统一生命周期、状态迁移规则和错误语义，用于统一：

- `apps/api/` 的接口返回语义
- `packages/application/` 的任务推进逻辑
- `apps/worker/` 的后台执行语义
- 前端轮询与错误展示逻辑
- `evals/` 中的失败分类与记录口径

本文档不负责：

- 定义正式结果字段内容
- 定义 Prompt 或 Provider 的策略细节
- 定义数据库表结构

## 核心原则

- 任务状态必须单一真源定义
- 错误类别必须显式化，不以自然语言替代结构语义
- 结果可用性与任务完成状态要区分
- 对外可见错误与内部诊断错误要分层
- 不允许用“伪成功结果”掩盖失败或阻断

## 任务实体关注点

一个评测任务在 `Phase 1` 中至少需要表达：

- `taskId`
- `status`
- `createdAt`
- `inputType`
- `title`
- `inputSummary`
- `errorCode`
- `errorMessage`
- `resultAvailable`
- `resultStatus`

说明：

- `status` 用于描述任务执行过程
- `resultStatus` 用于描述结果可读性语义
- 两者不能混为一个字段
- `resultAvailable` 应视为 `resultStatus` 的派生布尔语义，而不是独立状态源
- 约定 `resultAvailable = (resultStatus == available)`

## 任务状态枚举

`Phase 1` 统一使用以下任务状态：

- `queued`
- `processing`
- `completed`
- `failed`

## 状态定义

### `queued`

含义：

- 任务已创建
- 尚未开始正式执行
- 或正在等待执行资源

进入条件：

- 任务创建成功
- 后端接受任务后登记成功

退出条件：

- 进入 `processing`
- 进入 `failed`

### `processing`

含义：

- 任务已进入正式执行阶段
- 正在运行基线评分链路

进入条件：

- 执行器开始处理该任务

退出条件：

- 进入 `completed`
- 进入 `failed`

### `completed`

含义：

- 任务执行流程已结束
- 不代表一定存在可展示的正式结果正文

进入条件：

- 执行流程完成
- 已形成最终任务结论

退出条件：

- 终态，不再迁移

说明：

- `completed` 后仍可能出现 `resultStatus=not_available`
- `completed` 后仍可能出现 `resultStatus=blocked`

### `failed`

含义：

- 任务执行流程未能完成
- 无法形成成功完成的任务结论

进入条件：

- 输入处理失败且不可继续
- 运行时异常且不可恢复
- 依赖故障且本次执行终止

退出条件：

- 终态，不再迁移

## 状态迁移规则

统一状态迁移：

```text
queued -> processing
queued -> failed
processing -> completed
processing -> failed
```

禁止状态迁移：

- `completed -> processing`
- `failed -> processing`
- `completed -> queued`
- `failed -> queued`

## 结果状态枚举

`Phase 1` 统一使用以下结果状态：

- `available`
- `not_available`
- `blocked`

说明：

- `fetch_failed` 是前端页面本地派生状态，不属于后端任务真源状态

## 结果状态定义

### `available`

含义：

- 存在满足正式展示条件的结构化结果
- 前端可以进入正式结果阅读态

### `not_available`

含义：

- 当前不存在可展示的正式结果
- 但这不一定意味着任务失败

典型场景：

- 任务刚完成，但结果尚未就绪
- 当前流程只完成了任务结论，未形成可展示结果

### `blocked`

含义：

- 结果不满足正式展示条件
- 系统明确阻断其作为正式结果返回

典型场景：

- 结果结构不合法
- 结果未满足正式校验规则
- 结果进入了受控阻断路径

## 任务状态与结果状态关系

### 合法组合

- `queued + not_available`
- `processing + not_available`
- `completed + available`
- `completed + not_available`
- `completed + blocked`
- `failed + not_available`

### 非推荐组合

- `failed + available`

说明：

- 若任务已经 `failed`，原则上不应再对外暴露正式结果正文

## 重试语义

### `Phase 1` 规则

- 文档定义重试语义，但不强制先实现复杂重试系统
- 若实现重试，必须保持任务状态语义一致
- 不允许通过静默重跑掩盖错误来源

### 推荐原则

- 可恢复错误可进入受控重试
- 不可恢复错误直接进入 `failed`
- 若重试发生，应记录内部诊断信息

## 取消语义

`Phase 1` 当前不要求支持任务取消。

说明：

- 后续若引入取消语义，应新增状态与迁移说明
- 在未正式定义前，不应由实现层私自扩展 `cancelled`

## 错误语义分层

### 一、用户输入错误

表示请求在系统边界上不满足要求。

典型类别：

- 输入缺失
- 输入类型非法
- 文件上传参数非法

建议错误码：

- `VALIDATION_ERROR`
- `INVALID_INPUT_TYPE`
- `EMPTY_TEXT`

### 二、任务对象错误

表示任务标识或任务状态不满足读取或处理条件。

建议错误码：

- `TASK_NOT_FOUND`
- `TASK_STATE_CONFLICT`

### 三、结果对象错误

表示结果当前不可读取或不可作为正式结果展示。

建议错误码：

- `RESULT_NOT_AVAILABLE`
- `RESULT_BLOCKED`
- `RESULT_NOT_FOUND`

### 四、契约错误

表示结构校验失败或内部输出不满足正式契约。

建议错误码：

- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`

### 五、执行链路错误

表示运行链路中的依赖或服务错误。

建议错误码：

- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

## 错误码命名规则

推荐规则：

- 全部使用大写下划线命名
- 优先表达稳定语义，而不是技术异常细节
- 同一错误码在不同接口中含义必须一致

## HTTP 状态码映射建议

- 输入校验失败：`400` 或 `422`
- 任务不存在：`404`
- 结果不存在：`404`
- 状态冲突：`409`
- 限流：`429`
- Provider / 依赖失败：`502` 或 `503`
- 内部未分类错误：`500`

## 用户可见错误 vs 内部诊断错误

### 用户可见错误

对外返回时至少包含：

- `code`
- `message`

要求：

- 语义清晰
- 不泄露内部 SDK、堆栈、密钥或敏感信息

### 内部诊断错误

内部可额外记录：

- 原始异常信息
- Provider 响应摘要
- 超时详情
- 重试次数
- 跟踪 ID

说明：

- 这些信息应在日志或内部追踪系统中保留
- 不作为正式 API 对外字段默认暴露

## 日志与追踪字段建议

建议内部至少记录：

- `taskId`
- `requestId`
- `status`
- `resultStatus`
- `errorCode`
- `providerId`
- `modelId`
- `promptVersion`
- `schemaVersion`

说明：

- `Phase 1` 前端首期不强制展示这些扩展信息
- 但后端和回归体系应尽量保留

## 与 API Envelope 的关系

统一规则：

- 接口调用成功时，不代表业务结果一定可展示
- `success=true` 可以与 `resultStatus=not_available` 或 `blocked` 同时成立
- 这是因为接口本身返回成功，而业务结果语义可能是“不可展示”

举例：

- `GET /api/tasks/{taskId}/result` 返回 `200` 且 `success=true`
- `data.resultStatus=blocked`
- 这表示“结果读取接口调用成功，但结果被业务规则阻断”

## 与 Evals 的关系

`evals/` 在记录执行结果时应至少区分：

- 输入错误导致失败
- Provider 失败导致失败
- 契约失败导致阻断
- 结果可用但质量待比对

说明：

- 任务失败与结果阻断要分别统计
- 不能只记录“成功/失败”二元结论

## 完成标准

满足以下条件时，可认为任务生命周期与错误语义已足以支撑开发：

- 前端、后端、Evals 对任务状态名称与含义一致
- 结果可用性不再被混入任务状态字段
- 每类主要失败场景都有稳定错误码归属
- 接口实现可以按统一规则映射 HTTP 状态码
- 不会再通过伪结果掩盖阻断或失败

## 与现有文档的关系

- API 边界见 `apps/api/contracts/api-v0-overview.md`
- 评分流程见 `docs/architecture/scoring-pipeline.md`
- 前端状态流见 `docs/architecture/frontend-task-and-state-flow.md`
- 前端最小 API 假设见 `docs/contracts/frontend-minimal-api-assumptions.md`
