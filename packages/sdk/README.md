# `packages/sdk`

## 模块角色

该目录用于为外部调用方提供稳定接口与共享类型定义。

## 当前仓库现实

- 当前目录只有 README
- 还没有 SDK 实现代码
- 当前前端或其他调用方若需消费接口，仍应直接基于 `apps/api/contracts/`、`docs/contracts/` 与 `packages/schemas/` 对齐

因此当前这里定义的是未来 SDK 的稳定边界，而不是已落地 SDK 产品。

## 目标

- 为调用方屏蔽底层接口细节
- 保持结构契约一致性
- 为未来开放调用场景预留位置
- 避免前端或其他消费者自行复制第二套类型系统

## 最小边界

SDK 如落地，至少应围绕以下对象提供稳定消费入口：

- `JointSubmissionRequest`
- `EvaluationTask`
- `EvaluationResultResource`
- `DashboardSummary`
- `HistoryList`
- `SuccessEnvelope` / `ErrorEnvelope`

## 原则

- SDK 必须服从 `packages/schemas/` 单一真源
- SDK 不得重写任务状态、结果状态和错误码语义
- SDK 不得引入前端专有 Prompt 选择或结果修复逻辑

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "JointSubmissionRequest|EvaluationTask|EvaluationResultResource|DashboardSummary|HistoryList|ErrorEnvelope" packages/sdk/README.md packages/schemas docs/contracts`

## DevFleet 使用约束

- SDK 相关 mission 必须明确是“类型导出”“客户端封装”还是“错误映射”
- 在实现代码尚未落地前，不得把 README 文本误写成“当前已有稳定 SDK”
