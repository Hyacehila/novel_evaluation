# `apps/worker`

该模块是独立 `uv` app，职责固定为回归与批处理，不是用户任务主执行面。

当前阶段只提供最小 standalone CLI skeleton，用于建立明确的 `batch` 与 `eval` 命令面，并保持终止型执行路径。

## 入口模式

- `batch`
- `eval`

## 当前已实现

- `uv` 独立工程骨架
- `worker.cli` 命令入口
- `batch` / `eval` 帮助命令
- 显式 `--dry-run` 占位执行路径

## 负责

- 为后续批处理能力预留命令面
- 为后续评测回归能力预留命令面
- 明确 worker 与 `apps/api` 的边界

## 不负责

- 承接用户页面提交任务
- 接管 `apps/api` 进程内任务推进
- 定义新的任务状态
- 定义新的错误码
- 实现真实批处理、真实评测回归、`EvalRecord`、`EvalReport` 或 `EvalBaseline`

## 当前使用方式

- `uv run --project apps/worker python -m worker.cli batch --help`
- `uv run --project apps/worker python -m worker.cli eval --help`
- `uv run --project apps/worker python -m worker.cli batch --dry-run`
- `uv run --project apps/worker python -m worker.cli eval --dry-run`

未传 `--dry-run` 时，命令会以非零状态退出，避免把 skeleton 误判为真实执行。

## 后续对接方向

- `packages/application/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `packages/schemas/`
- `evals/`

这些依赖保留给后续波次接线；当前 skeleton 不直接接管正式运行时逻辑。
