# `packages/schemas/evals`

该子域用于放置正式评测与回归 schema。

## 正式文件颗粒度

- `case.py`
- `record.py`
- `baseline.py`
- `report.py`

## 正式对象

- `EvalCase`
- `EvalRecord`
- `EvalBaseline`
- `EvalReport`

## 冻结结论

- `EvalReport` 统一为单一正式对象
- `reportType` 固定为：
  - `execution_summary`
  - `baseline_comparison`
- `EvalBaseline` 独立存在

## 作用边界

- 为 runner、report、baseline 提供结构真源
- 不反向定义正式业务结果字段
