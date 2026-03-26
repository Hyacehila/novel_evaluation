# Canonical Schema Index

## 文档目的

本文档维护对象级 schema 索引、当前实现状态和正式文件归属。

## 状态词表

- `implemented`：正式 schema 已存在
- `doc_frozen`：字段与文件归属已冻结，但代码尚未落地
- `reserved`：未来扩展保留位

## 共享基础对象

| 对象 | 状态 | 正式真源文件 | 说明 |
| --- | --- | --- | --- |
| `SchemaModel` | `implemented` | `packages/schemas/common/base.py` | 共享基类 |
| `MetaData` | `implemented` | `packages/schemas/common/base.py` | 分页与响应元信息 |

## 输入与任务对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `ManuscriptChapter` | `implemented` | `packages/schemas/input/manuscript.py` |
| `ManuscriptOutline` | `implemented` | `packages/schemas/input/manuscript.py` |
| `Manuscript` | `implemented` | `packages/schemas/input/manuscript.py` |
| `JointSubmissionRequest` | `implemented` | `packages/schemas/input/joint_submission.py` |
| `InputScreeningResult` | `implemented` | `packages/schemas/input/screening.py` |
| `EvaluationTask` | `implemented` | `packages/schemas/output/task.py` |
| `EvaluationTaskSummary` | `implemented` | `packages/schemas/output/task.py` |
| `RecentResultSummary` | `implemented` | `packages/schemas/output/task.py` |
| `DashboardSummary` | `implemented` | `packages/schemas/output/dashboard.py` |
| `HistoryList` | `implemented` | `packages/schemas/output/dashboard.py` |

## 阶段对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `RubricEvaluationEvidenceRef` | `implemented` | `packages/schemas/stages/rubric.py` |
| `RubricEvaluationItem` | `implemented` | `packages/schemas/stages/rubric.py` |
| `RubricEvaluationSet` | `implemented` | `packages/schemas/stages/rubric.py` |
| `ConsistencyConflict` | `implemented` | `packages/schemas/stages/consistency.py` |
| `ConsistencyCheckResult` | `implemented` | `packages/schemas/stages/consistency.py` |
| `AggregatedRubricResult` | `implemented` | `packages/schemas/stages/aggregation.py` |
| `FinalEvaluationProjection` | `implemented` | `packages/schemas/output/result.py` |

## 正式结果对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `PlatformRecommendation` | `implemented` | `packages/schemas/output/result.py` |
| `DetailedAnalysis` | `implemented` | `packages/schemas/output/result.py` |
| `EvaluationResult` | `implemented` | `packages/schemas/output/result.py` |
| `EvaluationResultResource` | `implemented` | `packages/schemas/output/result.py` |
| `ErrorObject` | `implemented` | `packages/schemas/output/error.py` |
| `SuccessEnvelope` | `implemented` | `packages/schemas/output/envelope.py` |
| `ErrorEnvelope` | `implemented` | `packages/schemas/output/envelope.py` |

## Evals 对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `EvalCase` | `implemented` | `packages/schemas/evals/case.py` |
| `EvalRecord` | `implemented` | `packages/schemas/evals/record.py` |
| `EvalBaseline` | `implemented` | `packages/schemas/evals/baseline.py` |
| `EvalReport` | `implemented` | `packages/schemas/evals/report.py` |

说明：

- `EvalReport` 统一为单一正式对象
- `reportType` 固定为 `execution_summary | baseline_comparison`
- 不再保留 `EvalReport` 结构或文件颗粒度待确认项

## 未来扩展保留位

| 对象/字段 | 状态 | 说明 |
| --- | --- | --- |
| 多用户字段 | `reserved` | `ownerRef/userId/workspaceId/tenantId` 保留到后续阶段 |

## 真源优先级

1. 已落地的 `packages/schemas/**/*.py`
2. 本文档
3. `docs/contracts/json-contracts.md`
4. `docs/contracts/rubric-stage-contracts.md`
5. 其它消费文档
