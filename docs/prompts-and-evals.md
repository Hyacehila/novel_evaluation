# Prompts And Evals

## Prompt 资产布局

`prompts/` 只保留当前正式评分主线资产：

- `prompts/registry/*.yaml`：按 `promptId` 维护 scope 与启用状态
- `prompts/versions/<promptId>/<promptVersion>.yaml`：按版本维护元数据
- `prompts/scoring/<stage>/<promptId>/<promptVersion>.md`：正式 Prompt 正文

当前正式 Prompt ID：

- `screening-default`
- `screening-degraded`
- `type-classification-default`
- `type-classification-degraded`
- `rubric-default`
- `rubric-degraded`
- `type-lens-default`
- `type-lens-degraded`
- `aggregation-default`
- `aggregation-degraded`

## 选择规则

`packages/prompt-runtime` 的 `FilePromptRuntime` 按以下顺序选 Prompt：

1. `stage`
2. `inputCompositionScope`
3. `evaluationModeScope`
4. `providerScope`
5. `modelScope`
6. `status` 优先 `active`，其次 `candidate`
7. `enabled = true`

正文路径固定为 `promptId + promptVersion`，registry 和 version 的 `schemaVersion / rubricVersion` 必须一致。

## 当前 Prompt 口径

- `rubric` Prompt 只允许输出当前 `RubricEvaluationSlice` 需要的字段：
  `requestedAxes`、`items`、`axisSummaries`、`missingRequiredAxes`、`riskTags`、`overallConfidence`
- `aggregation` Prompt 只允许输出当前 `AggregatedRubricResult` 需要的字段：
  `overallVerdictDraft`、`verdictSubQuote`、`overallSummaryDraft`、`platformCandidates`、`marketFitDraft`、`strengthCandidates`、`weaknessCandidates`、`riskTags`、`overallConfidence`
- 当前 Prompt 与文档禁止再出现旧四分字段、旧骨架字段和旧聚合别名

## `evals/` 结构

- `evals/datasets/`：样本输入
- `evals/cases/`：suite JSON 和 case 引用
- `evals/runners/`：最小 runner
- `evals/reports/`：运行报告输出目录
- `evals/baselines/`：baseline 输出目录

`apps/worker` 通过共享 runtime 运行 `eval` / `batch`，不会分叉出第二套评分主线。

## 常用命令

```powershell
uv run --project apps/worker worker eval --suite smoke --dry-run
uv run --project apps/worker worker eval --suite smoke --report-id smoke_report --baseline-id smoke_baseline
uv run --project apps/worker worker batch --source .\path\to\batch.json --report-id batch_report
```

## 仓库卫生检查

仓库卫生脚本：

```powershell
.\scripts\repo\check-hygiene.ps1
```

当前固定检查三类问题：

- 空壳/禁用目录回流
- 旧 docs 子目录回流
- 现行 `docs/` 与 `prompts/` 出现旧字段或旧语义
