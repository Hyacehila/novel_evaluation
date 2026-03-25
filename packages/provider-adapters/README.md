# `packages/provider-adapters`

该模块用于实现正式 provider contract。

## 当前冻结结论

- `Phase 1` 唯一正式 Provider：`DeepSeek API`
- 上层统一依赖 `ProviderExecutionRequest/Success/Failure`
- 失败类型统一映射到：
  - `PROVIDER_FAILURE`
  - `TIMEOUT`
  - `DEPENDENCY_UNAVAILABLE`
  - `CONTRACT_INVALID`

## 负责

- 构造 Provider 请求
- 归一化原始响应
- 统一 `providerRequestId`
- 统一 `durationMs`
- 统一 `retryable`

## 不负责

- 定义任务状态
- 定义结果结构
- 定义 Prompt 选择

## 真源

- 高层边界：`docs/architecture/provider-abstraction.md`
- 正式 contract：`docs/contracts/provider-execution-contract.md`
