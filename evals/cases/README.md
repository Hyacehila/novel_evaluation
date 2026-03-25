# `evals/cases`

该目录用于组织结构化评测用例。

## 子目录

- `scoring/`
- `robustness/`
- `regression/`

## `EvalCase` 最小信息

- `caseId`
- `datasetRef`
- `inputComposition`
- `goal`
- `expectedOutcomeType`
- `includedInBaseline`

## 规则

- case 只组织评测输入与预期，不定义正式业务字段
- regression case 必须可关联 baseline comparison
