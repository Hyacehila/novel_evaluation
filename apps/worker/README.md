# `apps/worker`

该模块是独立 `uv` app，职责固定为回归与批处理，不是用户任务主执行面。

## 入口模式

- `batch`
- `eval`

## 负责

- 运行批量任务
- 运行评测回归
- 写出 `EvalRecord`
- 生成 `EvalReport` 与 `EvalBaseline` 相关产物

## 不负责

- 承接用户页面提交任务
- 定义新的任务状态
- 定义新的错误码

## 依赖

- `packages/application/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `packages/schemas/`
- `evals/`
