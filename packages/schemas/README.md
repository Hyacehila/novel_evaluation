# `packages/schemas`

该目录用于维护系统输入输出的正式结构定义。

## 目标

- 成为严格 JSON 契约的唯一真源
- 统一 API、Worker、Evals 对结构的理解
- 为版本演进提供边界

## 原则

- 任何结构变更都应有文档与评测支撑
- 不允许多个位置重复定义核心结构
- `Pydantic` 可以承担 API 边界与运行时校验，但不替代本目录成为正式结构真源
- Prompt、Provider、Application 与 API 都必须围绕本目录定义的正式结构协同
