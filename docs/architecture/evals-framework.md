# Evals 框架说明

## 文档目的

本文档冻结 `Phase 1` 的回归评测框架结构、对象关系和统一报告口径。

## 目标

- 验证正式结构是否稳定
- 验证评分主线是否漂移
- 验证 Prompt/Schema/Provider 变化影响
- 生成结构化 baseline 与 report

## 正式对象

- `EvalCase`
- `EvalRecord`
- `EvalBaseline`
- `EvalReport`

`EvalReport` 固定为单一正式对象，并新增：

- `reportType = execution_summary | baseline_comparison`

`EvalBaseline` 继续独立存在，不并入 `EvalReport`。

## 文件颗粒度

`packages/schemas/evals/` 正式文件颗粒度固定为：

- `case.py`
- `record.py`
- `baseline.py`
- `report.py`

## 执行面

- 用户主任务不通过 worker/evals
- worker 只运行 `batch` 与 `eval`
- eval runner 输出 `EvalRecord`
- report/baseline 基于 `EvalRecord` 汇总

## 触发规则

以下变更必须触发一次受控回归：

- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 上传与输入边界
- 任务状态或错误码集合

## 最小结果

每次回归至少要能回答：

- 哪些 case 被执行
- 哪些结果 `available / blocked / failed`
- 正式结构是否合法
- 与 baseline 相比发生了什么变化

## 非目标

- 复杂在线评测后台
- 多 Provider 生产矩阵
- 第二套业务结果语义
