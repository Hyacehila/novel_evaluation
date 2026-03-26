# `packages/provider-adapters`

该模块用于实现正式 provider contract。

## 当前实现

- `src/provider_adapters/contracts.py`：`ProviderExecutionRequest/Success/Failure`、冻结 `rawJson` 与失败映射辅助函数
- `src/provider_adapters/base.py`：最小 `ProviderAdapter` 协议
- `src/provider_adapters/local.py`：不访问外网的本地 deterministic adapter

## 公开导出

- `ProviderExecutionRequest`
- `ProviderExecutionSuccess`
- `ProviderExecutionFailure`
- `ProviderFailureType`
- `ProviderAdapter`
- `LocalAdapterMode`
- `LocalDeterministicProviderAdapter`
- `build_provider_failure`
- `map_failure_type_to_error_code`

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
