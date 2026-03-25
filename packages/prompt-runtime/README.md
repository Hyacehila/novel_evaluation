# `packages/prompt-runtime`

## 模块角色

该目录用于承载 Prompt 运行时治理能力。

## 当前仓库现实

- 当前目录只有 README
- 还没有正式 Prompt runtime 实现代码
- 当前仓库中的 Prompt 治理仍停留在 `prompts/` README 合同层

因此当前这里定义的是运行时能力边界，而不是现成 runtime 实现。

## 典型职责

- Prompt 加载
- Prompt 变量渲染
- Prompt 版本选择
- Prompt 守卫与约束检查
- 向应用层与编排层暴露统一 Prompt Runtime 接口

## 集成关系

- Prompt 文件真源位于 `prompts/`
- `packages/application/` 后续通过本目录选择和渲染正式 Prompt
- `apps/api/` 与未来 `apps/worker/` 应依赖上层 application / runtime 边界，而不是自行选择 Prompt

## 原则

- Prompt 文件和 Prompt 运行时能力分离
- 前者存放于 `prompts/`，后者沉淀在 `packages/`
- 运行时不成为 Prompt 正文真源
- 不允许绕过正式资产目录直接内嵌长期 Prompt
- 不允许前端或 API 路由层直接持有正式评分 Prompt 正文

## 不负责

- 存放 Prompt 正文本体
- 代替 registry / version 台账
- 定义正式 schema 结构
- 重写评分主线阶段定义

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "Prompt 加载|Prompt 变量渲染|Prompt 版本选择|prompts/|运行时不成为 Prompt 正文真源" packages/prompt-runtime/README.md prompts/README.md`

## DevFleet 使用约束

- Prompt runtime 相关 mission 必须明确是“加载”“选择”“渲染”还是“守卫检查”
- 在实现代码尚未落地前，不得把 README 文本误写成“当前已具备正式 runtime 行为”
