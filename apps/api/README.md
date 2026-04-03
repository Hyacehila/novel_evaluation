# `apps/api`

本目录只负责 HTTP 边界和任务入口。运行时装配在 `packages/runtime/`，业务编排在 `packages/application/`，正式字段真源在 `packages/schemas/`。

常用命令：

- `uv sync --project apps/api`
- `uv run --project apps/api uvicorn api.app:app --reload --host 127.0.0.1 --port 8000`
- `uv run --project apps/api pytest apps/api/tests evals/tests`

当前固定路由：

- `GET /api/provider-status`
- `POST /api/provider-status/runtime-key`
- `DELETE /api/provider-status/runtime-key`
- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

继续阅读：

- [`../../docs/runbook.md`](../../docs/runbook.md)
- [`../../docs/contracts.md`](../../docs/contracts.md)
- [`../../docs/architecture.md`](../../docs/architecture.md)
