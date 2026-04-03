# `apps/web`

本目录是本地 UI。它消费同源 `/api`，并把后端结果映射成页面视图；`apps/web/src/api/contracts.ts` 只是前端镜像，不是正式契约真源。

页面路由：

- `/`
- `/tasks/new`
- `/tasks/{taskId}`
- `/tasks/{taskId}/result`
- `/history`

常用命令：

- `pnpm --dir apps/web install`
- `pnpm --dir apps/web dev -- --hostname 127.0.0.1 --port 3000`
- `pnpm --dir apps/web test`
- `pnpm --dir apps/web build`
- `pnpm --dir apps/web test:e2e`

E2E 默认使用 deterministic provider；真实 `DeepSeek` 只在 `startup_key` / `runtime_key` 模式下做补充验收。

继续阅读：

- [`../../docs/runbook.md`](../../docs/runbook.md)
- [`../../docs/contracts.md`](../../docs/contracts.md)
- [`../../docs/architecture.md`](../../docs/architecture.md)
