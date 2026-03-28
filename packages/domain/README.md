# `packages/domain`

## 模块角色

该模块承载当前仓库的核心领域对象与共享业务词表，是 `packages/application/`、`packages/schemas/`、`apps/api/`、`apps/worker/` 与 `evals/` 的共同上游语义层。

## 主要输出对象

该模块未来定义或承接的核心对象包括：

- `Manuscript`
- `JointSubmissionRequest`
- `EvaluationTask`
- `EvaluationTaskSummary`
- `EvaluationResult`
- `EvaluationResultResource`
- `EvalRecord`
- 共享词表：
  - `inputComposition`
  - `evaluationMode`
  - `status`
  - `resultStatus`

## 主要职责

- 冻结领域对象语义
- 冻结对象不变量与派生字段
- 冻结共享词表
- 为 application / schema / API 提供共同起点

## 不负责

- 定义 API 路径
- 定义前端 View Model
- 定义 Prompt 正文
- 执行模型调用
- 直接承担数据库或网络 side effects

## 输入依赖

该模块依赖的上游真源主要是：

- `docs/architecture/domain-model.md`
- `docs/contracts/canonical-schema-index.md`
- `docs/contracts/rubric-stage-contracts.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`

## 下游消费者

- `packages/application/`
- `packages/schemas/`
- `apps/api/`
- `apps/worker/`
- `evals/`

## 错误语义

- 本模块只定义错误语义归属，不直接发明 API envelope
- 状态与错误码含义必须沿用上游冻结文档
- 不允许下游模块绕过本模块重新定义任务与结果状态

## Side Effects

- 本模块本身不应承担网络、文件或运行时调用 side effects
- 若后续实现需要序列化、持久化或适配层映射，应由下游模块处理

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "Manuscript|EvaluationTask|EvaluationResult|EvaluationResultResource|不变量|派生字段|关系" docs/architecture/domain-model.md packages/domain/README.md`

## DevFleet 使用约束

- 后续与领域对象相关的实现 mission 必须先读取本文档和 `docs/architecture/domain-model.md`
- 不得在 API DTO、前端消费对象或 worker 内部反向定义第二套正式领域对象
