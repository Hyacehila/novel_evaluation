# `packages/prompt-runtime`

该目录用于承载 Prompt 运行时治理能力。

## 典型职责

- Prompt 加载
- Prompt 变量渲染
- Prompt 版本选择
- Prompt 守卫与约束检查

## 原则

- Prompt 文件和 Prompt 运行时能力分离
- 前者存放于 `prompts/`，后者沉淀在 `packages/`
