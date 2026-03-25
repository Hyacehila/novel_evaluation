# `evals/baselines`

该目录用于存放历史评测基线。

## 正式对象

- `EvalBaseline`

## 最小字段

- `baselineId`
- `caseIds`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `createdAt`

## 规则

- baseline 独立于 report
- baseline 不能被新结果直接覆盖
- baseline comparison 通过 `EvalReport(reportType=baseline_comparison)` 表达
