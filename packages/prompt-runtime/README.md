# `packages/prompt-runtime`

该目录用于承载 Prompt 运行时治理能力。

## 典型职责

- Prompt 加载
- Prompt 变量渲染
- Prompt 版本选择
- Prompt 守卫与约束检查
- 向应用层与编排层暴露统一 Prompt Runtime 接口

## 集成关系

- Prompt 文件真源位于 `prompts/`
- `packages/application/` 通过本目录选择和渲染正式 Prompt
- `PocketFlow` 组织多阶段执行时，应复用本目录暴露的 Prompt Runtime 能力

## 原则

- Prompt 文件和 Prompt 运行时能力分离
- 前者存放于 `prompts/`，后者沉淀在 `packages/`
- 运行时不成为 Prompt 正文真源
- 不允许绕过正式资产目录直接内嵌长期 Prompt
