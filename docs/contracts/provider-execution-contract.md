# Provider 运行时 I/O 契约

## 文档目的

本文档冻结 `Phase 1` 的最小 provider port，供 `packages/provider-adapters/`、`packages/application/`、`apps/worker/` 和 `evals/` 统一使用。

## 对象集合

- `ProviderExecutionRequest`
- `ProviderExecutionSuccess`
- `ProviderExecutionFailure`

## `ProviderExecutionRequest`

最小必需字段：

- `taskId`
- `stage`
- `promptId`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `requestId`
- `messages`

推荐补充字段：

- `inputComposition`
- `evaluationMode`
- `timeoutMs`
- `responseFormat`

约束：

- `stage` 必须使用正式阶段名
- `promptId` 与 `promptVersion` 必须来自正式 Prompt 资产
- `requestId` 用于日志、诊断和 provider 请求关联

## `ProviderExecutionSuccess`

最小必需字段：

- `providerId`
- `modelId`
- `requestId`
- `providerRequestId`
- `durationMs`
- `rawText`
- `rawJson`

约束：

- `durationMs` 统一使用毫秒
- `providerRequestId` 可为空，但字段必须保留
- `rawJson` 仅表示 provider 返回的结构化内容，不等同于正式业务结果

## `ProviderExecutionFailure`

最小必需字段：

- `providerId`
- `modelId`
- `requestId`
- `providerRequestId`
- `durationMs`
- `failureType`
- `message`
- `retryable`

`failureType` 冻结集合：

- `provider_failure`
- `timeout`
- `dependency_unavailable`
- `contract_invalid`

## 与正式错误码映射

`failureType` 必须映射到现有错误码：

- `provider_failure -> PROVIDER_FAILURE`
- `timeout -> TIMEOUT`
- `dependency_unavailable -> DEPENDENCY_UNAVAILABLE`
- `contract_invalid -> CONTRACT_INVALID`

说明：

- 业务阻断不属于 provider failure 分类
- 结构校验失败仍由 application/schema 层决定是否映射为 `RESULT_SCHEMA_INVALID` 或 `STAGE_SCHEMA_INVALID`

## 重试边界

- `retryable` 只表达 provider 内部可否重试
- provider 内部重试不得改变 `taskId`
- provider 内部重试不得生成第二份正式结果

## 适配层责任

`packages/provider-adapters/` 负责：

- 构造 `ProviderExecutionRequest`
- 归一化成功/失败对象
- 屏蔽 SDK 字段差异
- 提供 `providerRequestId`、`durationMs`、`retryable`

不负责：

- 决定任务状态
- 决定正式结果是否合法
- 直接产出 `EvaluationResult`
