# Provider 抽象说明

本文档说明模型供应商适配层的目标、边界与当前冻结结论。

## 当前结论

- `Phase 1` 默认且唯一正式接入的模型 Provider 为 `DeepSeek API`
- 上层仍然通过 `packages/provider-adapters/` 依赖统一抽象，而不是直接依赖 Provider SDK
- Provider 抽象边界保留，用于未来扩展其它 Provider，但这不是当前实现前提

## 目标

- 收敛 `DeepSeek API` 的调用细节
- 隐藏底层 SDK、鉴权与错误格式差异
- 为上层提供稳定的请求与响应接口
- 为未来扩展和回归比较保留抽象边界

## 抽象边界

Provider 适配层需要统一处理：

- 请求构造
- 模型选择
- 响应读取
- 异常分类
- 超时控制
- 重试策略
- 日志上下文

## 上层不应感知的内容

- 具体厂商 SDK 类型
- 各家接口字段差异
- 供应商独有错误格式
- 供应商特有鉴权方式
- `DeepSeek API` 的底层请求细节

## 与其它模块的关系

- 上游依赖 `packages/application` 与 `packages/prompt-runtime`
- 编排层通过 `PocketFlow` 消费统一 Provider 调用能力
- 下游连接当前正式实现 `DeepSeek API`，并为未来扩展预留适配点
- 输出结果必须回到统一 JSON 契约与 `packages/schemas/` 的正式结构语义

## Phase 1 不做的事情

- 多 Provider 动态路由
- 多 Provider 线上 A/B
- 前端选择正式 Provider
- 在 `apps/api` 或 `packages/application` 中直接写死 SDK 调用

## 设计要求

- Provider 细节必须收敛在 `packages/provider-adapters/`
- 上层只消费统一错误语义与统一响应结构
- Provider 替换不应迫使领域模型和应用流程重写
- 评测与回归可以复用同一套 Provider 抽象边界
