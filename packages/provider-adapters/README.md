# `packages/provider-adapters`

该目录用于封装模型供应商适配逻辑。

## 目标

- 屏蔽不同供应商之间的接口差异
- 为应用层提供统一调用入口
- 收敛鉴权、错误格式、超时与重试等 Provider 细节
- 为未来 Provider 扩展和回归验证保留抽象边界

## 当前实现基线

- `Phase 1` 默认且唯一正式接入的模型 Provider 为 `DeepSeek API`
- 上层仍应依赖统一抽象，而不是直接依赖 `DeepSeek API` SDK 细节

## 原则

- 不向上层暴露供应商 SDK 细节
- 不将供应商特有结构泄漏到领域模型中
- 不在 `apps/api` 或 `packages/application` 中直接写死 Provider 请求细节
