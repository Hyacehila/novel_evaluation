# `apps/api`

该目录承载服务端接口层，是本地单用户版本的主要任务执行入口。

## 当前实现

- 语言与环境：`Python 3.13 + uv`
- Web API 框架：`FastAPI`
- 边界 DTO 与运行时校验：`Pydantic`
- 状态持久化：`SQLite`
- Provider 行为：有 `DeepSeek API Key` 时走真实 Provider；缺失时 API 仍可只读启动，但不能创建新分析任务
- 用户任务执行：由 API 进程内完成创建、推进、恢复和结果读取；若通过前端录入一次性 runtime key，则仅在当前 API 进程内生效
- 结果兼容：旧版或损坏的持久化结果不会伪装成成功结果，而会在读取时降级为 `not_available`

## 职责

- 接收并校验外部请求
- 调用应用层能力完成任务创建、任务读取与结果读取
- 在进程内推进用户任务并在启动时恢复未完成任务
- 对前端提供稳定接口、provider 状态与错误语义
- 返回统一 envelope 与正式结构化结果

## 设计原则

- 只做接口边界与流程编排，不承载底层 Provider 细节
- 不直接拼接正式 Prompt
- 不重新定义正式结果真源
- 所有输出必须符合严格 JSON 契约

## 常用命令

- 安装依赖：`uv sync --project apps/api`
- 启动开发服务：`uv run --project apps/api uvicorn api.app:app --reload --host 127.0.0.1 --port 8000`
- 运行测试：`uv run --project apps/api pytest .\apps\api\tests .\evals\tests`
- 运行语法检查：`uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages .\evals`

## 当前路由

- `GET /api/provider-status`
- `POST /api/provider-status/runtime-key`
- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`
