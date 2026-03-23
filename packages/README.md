# `packages`

该目录用于承载可复用核心能力，是系统长期演进的主战场。

## 当前子目录

- `domain/`：领域对象与评分规则
- `application/`：用例编排与流程组织
- `provider-adapters/`：模型供应商适配层
- `schemas/`：正式结构契约
- `prompt-runtime/`：Prompt 运行时治理能力
- `shared/`：配置、日志、错误与通用工具
- `sdk/`：客户端接口与共享类型

## 原则

- 业务核心能力优先沉淀到 `packages/`
- 不让应用入口层承担过多复用逻辑
- 不让研究产物侵入正式模块
