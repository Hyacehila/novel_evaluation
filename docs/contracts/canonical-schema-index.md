# Canonical Schema Index

## 文档目的

本文档维护对象级 schema 索引、当前实现状态和正式文件归属。

## 状态词表

- `implemented`：正式 schema 已存在
- `reserved`：未来扩展保留位

## 共享基础对象

| 对象 | 状态 | 正式真源文件 | 说明 |
| --- | --- | --- | --- |
| `SchemaModel` | `implemented` | `packages/schemas/common/base.py` | 共享基类 |
| `MetaData` | `implemented` | `packages/schemas/common/base.py` | 分页与响应元信息 |
| `NovelType` | `implemented` | `packages/schemas/common/enums.py` | 当前正式类型枚举 |
| `TypeLensDefinition` | `implemented` | `packages/schemas/common/novel_types.py` | 类型 lens 目录定义 |

## 输入与任务对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `ManuscriptChapter` | `implemented` | `packages/schemas/input/manuscript.py` |
| `ManuscriptOutline` | `implemented` | `packages/schemas/input/manuscript.py` |
| `Manuscript` | `implemented` | `packages/schemas/input/manuscript.py` |
| `JointSubmissionRequest` | `implemented` | `packages/schemas/input/joint_submission.py` |
| `RuntimeProviderKeyRequest` | `implemented` | `packages/schemas/input/provider_configuration.py` |
| `EvaluationTask` | `implemented` | `packages/schemas/output/task.py` |
| `EvaluationTaskSummary` | `implemented` | `packages/schemas/output/task.py` |
| `RecentResultSummary` | `implemented` | `packages/schemas/output/task.py` |
| `DashboardSummary` | `implemented` | `packages/schemas/output/dashboard.py` |
| `HistoryList` | `implemented` | `packages/schemas/output/dashboard.py` |
| `ProviderStatus` | `implemented` | `packages/schemas/output/provider_status.py` |

## 阶段对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `InputScreeningResult` | `implemented` | `packages/schemas/input/screening.py` |
| `TypeClassificationCandidate` | `implemented` | `packages/schemas/stages/type_classification.py` |
| `TypeClassificationResult` | `implemented` | `packages/schemas/stages/type_classification.py` |
| `RubricEvaluationEvidenceRef` | `implemented` | `packages/schemas/stages/rubric.py` |
| `RubricEvaluationItem` | `implemented` | `packages/schemas/stages/rubric.py` |
| `RubricEvaluationSlice` | `implemented` | `packages/schemas/stages/rubric.py` |
| `RubricEvaluationSet` | `implemented` | `packages/schemas/stages/rubric.py` |
| `TypeLensItem` | `implemented` | `packages/schemas/stages/type_lens.py` |
| `TypeLensEvaluationResult` | `implemented` | `packages/schemas/stages/type_lens.py` |
| `ConsistencyConflict` | `implemented` | `packages/schemas/stages/consistency.py` |
| `ConsistencyCheckResult` | `implemented` | `packages/schemas/stages/consistency.py` |
| `PlatformCandidate` | `implemented` | `packages/schemas/stages/aggregation.py` |
| `AggregatedRubricResult` | `implemented` | `packages/schemas/stages/aggregation.py` |
| `FinalEvaluationProjection` | `implemented` | `packages/schemas/output/result.py` |

## 正式结果对象

| 对象 | 状态 | 正式真源文件 |
| --- | --- | --- |
| `AxisEvaluationResult` | `implemented` | `packages/schemas/output/result.py` |
| `OverallEvaluationResult` | `implemented` | `packages/schemas/output/result.py` |
| `TypeAssessmentResult` | `implemented` | `packages/schemas/output/result.py` |
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
