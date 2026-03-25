# `packages/schemas/stages`

## 子域角色

该子域用于放置正式评分主线的后端内部阶段对象 schema。

## 当前正式对象

当前已经实际落地：

- `packages/schemas/stages/rubric.py`
  - `RubricEvaluationEvidenceRef`
  - `RubricEvaluationItem`
  - `RubricEvaluationSet`
- `packages/schemas/stages/consistency.py`
  - `ConsistencyConflict`
  - `ConsistencyCheckResult`
- `packages/schemas/stages/aggregation.py`
  - `AggregatedRubricResult`

## 作用边界

- 冻结后端内部阶段对象结构
- 为 `packages/application/` 提供稳定阶段输入输出
- 不直接作为前端正式结果 DTO

## 当前边界说明

- `InputScreeningResult` 当前仍放在 `packages/schemas/input/screening.py`，不属于本子域已落地对象
- `FinalEvaluationProjection` 当前放在 `packages/schemas/output/result.py`，因为它已经接近对外结果边界
- 若未来调整阶段对象归属，必须先更新 `docs/contracts/canonical-schema-index.md`

## 不负责

- 定义任务资源与结果资源路径
- 定义前端页面消费对象
- 发明新的评分主线分支或 `pairwise` 结构

## 验收方式

- `git diff --check`
- `rg "RubricEvaluationEvidenceRef|RubricEvaluationItem|RubricEvaluationSet|ConsistencyConflict|ConsistencyCheckResult|AggregatedRubricResult" docs/contracts/canonical-schema-index.md packages/schemas/stages/README.md`
