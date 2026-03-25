# `evals`

该目录承载正式回归与批处理体系。

## 目标

- 为 Prompt/Schema/Provider 变化提供受控回归
- 输出 `EvalRecord`
- 汇总 `EvalBaseline`
- 汇总 `EvalReport`

## 冻结结论

- `EvalReport` 统一为单一正式对象
- `reportType = execution_summary | baseline_comparison`
- 用户主任务不经过 `evals`
- `worker` 只运行 `batch/eval`

## 子目录

- `datasets/`
- `cases/`
- `runners/`
- `reports/`
- `baselines/`

## 必须触发回归的变化

- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 输入/上传边界
- 状态与错误码语义
