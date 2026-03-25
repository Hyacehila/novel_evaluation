# `packages/schemas/evals`

## 子域角色

该子域用于放置正式评测与回归相关 schema。

## 目标对象

根据 `docs/contracts/canonical-schema-index.md`，当前主要承接：

- `EvalCase`
- `EvalRecord`
- `EvalBaseline`
- `EvalReport`

## 当前状态

当前该子域只有 `README.md`，尚无正式 `.py` schema 类落地。

因此当前状态应理解为：

- 对象语义已在文档层冻结
- 正式 schema 仍为 `schema_pending`
- 本 README 不能被误认成已实现证明

## 作用边界

- 预留结构化评测样本对象落位目录
- 预留单次评测记录对象落位目录
- 预留基线记录与报告对象落位目录
- 不反向定义正式业务结果字段

## 当前待确认项

- `EvalReport` 是否拆分为基线报告与比较报告两类正式结构
- 基线与报告对象的最小公共字段集合
- `case / record / baseline / report` 的最终文件拆分颗粒度

## 验收方式

- `git diff --check`
- `rg "EvalCase|EvalRecord|EvalBaseline|EvalReport|schema_pending" docs/contracts/canonical-schema-index.md packages/schemas/evals/README.md`
