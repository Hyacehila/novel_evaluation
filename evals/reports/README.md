# `evals/reports`

该目录用于存放结构化回归报告。

## 正式对象

- `EvalReport`

## 冻结字段关注点

- `reportId`
- `reportType`
- `caseIds`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `createdAt`

## `reportType`

- `execution_summary`
- `baseline_comparison`

## 规则

- report 不替代 baseline
- report 必须能回答哪些 case `available / blocked / failed`
