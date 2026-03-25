# Provider 抽象说明

## 当前结论

- `Phase 1` 默认且唯一正式接入的 Provider 为 `DeepSeek API`
- 上层统一依赖 `ProviderExecutionRequest/Success/Failure`
- Provider 细节必须收敛在 `packages/provider-adapters/`

## 抽象目标

- 屏蔽 SDK 字段差异
- 屏蔽鉴权差异
- 统一失败分类
- 统一 `providerRequestId` 与 `durationMs`
- 让 application 只感知 provider contract，而不是 SDK

## 最小 contract

正式 contract 真源在：

- `docs/contracts/provider-execution-contract.md`

高层文档不再重复定义第二套字段集合。

## 适配层负责

- 构造 provider 请求
- 设置模型与超时
- 接收原始响应
- 归一化为 success/failure
- 输出 `retryable`

## 适配层不负责

- 决定任务状态
- 决定是否业务阻断
- 输出 `EvaluationResult`
- 定义前端展示逻辑

## 当前不做

- 多 Provider 动态路由
- 多 Provider 线上 A/B
- 前端选择正式 Provider
- `apps/api` 或 `packages/application` 直接写 SDK
