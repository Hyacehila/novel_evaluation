# `apps/api`

该目录用于承载服务端接口层。

## 当前实现基线

- 语言与环境：`Python 3.13 + uv`
- Web API 框架：`FastAPI`
- 边界 DTO 与运行时校验：`Pydantic`
- 正式模型调用：通过 `packages/provider-adapters/` 接入，`Phase 1` 默认使用 `DeepSeek API`
- 多阶段评分编排：优先复用 `PocketFlow`

## 职责

- 接收并校验外部请求
- 调用应用层能力完成任务创建、任务读取与结果读取
- 对前端提供稳定接口与错误语义
- 返回统一 envelope 与正式结构化结果

## 设计原则

- 只做接口边界与流程编排，不承载底层 Provider 细节
- 不直接拼接正式 Prompt
- 不重新定义正式结果真源
- 所有输出必须符合严格 JSON 契约

## 当前初始化状态

- 已在本目录建立 Python `uv` 工程基线
- Python 版本基线为 `3.13`
- 后端技术路线已冻结到 `FastAPI + Pydantic + DeepSeek API + PocketFlow`
- 当前仍以结构和实现准备为主，尚未进入大规模业务开发
- 后续执行 Python 命令统一使用 `uv run`
