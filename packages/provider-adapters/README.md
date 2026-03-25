# `packages/provider-adapters`

## 模块角色

该目录用于封装模型供应商适配逻辑，为应用层提供统一 Provider 抽象边界。

## 当前仓库现实

- 当前目录只有 README
- 还没有任何正式 Provider adapter 实现代码
- 当前应用层 `packages/application/services/evaluation_service.py` 仅写入占位元数据：
  - `providerId = provider-local`
  - `modelId = model-local`

因此当前这里定义的是适配层合同，而不是已落地的外部 Provider 集成。

## 目标

- 屏蔽不同供应商接口差异
- 为应用层提供统一调用入口
- 收敛鉴权、错误格式、超时与重试等 Provider 细节
- 为未来 Provider 扩展和回归验证保留抽象边界

## 最小输入 / 输出边界

### 输入

- 已渲染的 Prompt
- 结构化执行上下文
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`

### 输出

- 原始 provider 响应
- 规范化后的执行结果或错误对象
- 可追踪的 provider / model 元数据

## 原则

- 不向上层暴露供应商 SDK 细节
- 不将供应商特有结构泄漏到领域模型中
- 不在 `apps/api` 或 `packages/application` 中直接写死 Provider 请求细节
- 不得借接入 Provider 为名复活多路径评分或第二套结果结构

## 不负责

- 定义正式 schema 真源
- 维护 Prompt 正文本体
- 决定任务状态和结果状态枚举
- 代替 application service 编排主流程

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "providerId|modelId|占位元数据|统一调用入口|错误格式|超时" packages/provider-adapters/README.md packages/application/services/evaluation_service.py docs/operations/rollback-and-fallback.md`

## DevFleet 使用约束

- Provider 相关 mission 必须明确是“抽象接口”“单一 adapter 实现”还是“错误归一化”
- 在实现代码尚未落地前，不得把 README 合同误写成“当前已正式接入外部 Provider”
