# `apps/worker`

该模块是独立 `uv` app，职责固定为回归与批处理，不是用户任务主执行面。

## 当前已实现

- `worker eval --suite <name> [--baseline-id <id>] [--report-id <id>] [--dry-run]`
- `worker batch --source <path> [--report-id <id>] [--dry-run]`
- 复用 `packages/application/services/evaluation_service.py` 的同一条正式评分主线
- 输出 `evals/reports/{reportId}.json`
- 输出 `evals/reports/{reportId}.records.json`
- 传入 `--baseline-id` 时输出 `evals/baselines/{baselineId}.json`

## 负责

- 跑回归 suite
- 跑本地批处理源文件
- 生成 baseline / report / records 工件
- 记录与主线一致的 `promptVersion / schemaVersion / rubricVersion / providerId / modelId`

## 不负责

- 承接用户页面提交任务
- 接管 `apps/api` 进程内任务推进
- 定义新的任务状态
- 定义新的错误码

## 当前使用方式

- `uv run --project apps/worker worker eval --help`
- `uv run --project apps/worker worker batch --help`
- `uv run --project apps/worker worker eval --suite smoke --dry-run`
- `uv run --project apps/worker worker eval --suite smoke --baseline-id baseline_smoke --report-id report_smoke`
- `uv run --project apps/worker worker batch --source .\path\to\batch.json --report-id batch_smoke`
