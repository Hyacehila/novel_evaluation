# `apps/worker`

本目录只负责 `eval` / `batch` CLI。它通过 `packages/runtime.worker` 获取共享 runtime，不再依赖 `apps/api` 内部装配。

命令：

- `uv run --project apps/worker worker eval --help`
- `uv run --project apps/worker worker batch --help`
- `uv run --project apps/worker worker eval --suite smoke --dry-run`
- `uv run --project apps/worker worker eval --suite smoke --baseline-id smoke_baseline --report-id smoke_report`
- `uv run --project apps/worker worker batch --source .\path\to\batch.json --report-id batch_report`

继续阅读：

- [`../../docs/runbook.md`](../../docs/runbook.md)
- [`../../docs/prompts-and-evals.md`](../../docs/prompts-and-evals.md)
- [`../../docs/architecture.md`](../../docs/architecture.md)
