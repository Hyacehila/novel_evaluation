# `evals`

## 目录角色

该目录用于承载正式评测与回归治理入口。

它的目标不是在当前阶段假装已经有完整 eval harness，而是把后续样本、case、runner、baseline、report 的边界、回归触发规则和最小记录要求冻结下来。

## 当前仓库现实

当前 `evals/` 已存在：

- `datasets/`
- `cases/`
- `runners/`
- `reports/`
- `baselines/`

但当前实际落地内容仍以 README 与 `.gitkeep` 占位为主：

- 还没有正式 `EvalCase` 实例文件
- 还没有正式 baseline 记录实例
- 还没有正式 report 实例
- 还没有 runner 脚本实现
- `packages/schemas/evals/` 也仍处于 README 级说明

因此当前 `evals/` 的状态是：

- 治理合同已冻结
- 执行实例与 schema 仍待后续窄 mission 落地

## 核心目标

`evals/` 当前至少要回答：

- 什么时候必须跑回归
- 回归至少比较哪些信息
- 结果至少要记录哪些元数据
- Prompt / Schema / Provider 变化后如何保持可追踪比较

## 与正式主线的关系

Evals 必须服务于当前单主线正式评分方案：

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

同时必须服从当前联合输入主线：

- `chapters_outline`
- `chapters_only`
- `outline_only`

说明：

- 不允许为旧多路径评分、`pairwise` 或伪结果展示单独设计正式 eval 主线
- `evals/` 不能反向定义第二套 schema 或结果语义

## 样本与回归最小要求

当前最小回归记录至少应关联：

- `caseId`
- `inputComposition`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 结果结构是否合法
- 任务是 `failed`、`blocked` 还是 `available`
- 顶层结果摘要或阻断 / 失败结论

## 何时必须触发受控回归

以下变化至少应触发一次受控回归审查：

- 正式 Prompt 版本变化
- `schemaVersion` 变化
- `rubricVersion` 变化
- `providerId` / `modelId` 变化
- 任务状态与结果状态语义变化
- 错误码集合变化
- 联合输入边界变化
- `fatalRisk` 词表变化

## 当前目录解释

- `datasets/`：样本、金标准、夹具治理入口
- `cases/`：结构化回归用例治理入口
- `runners/`：执行入口合同
- `reports/`：报告产物合同
- `baselines/`：基线记录合同

## 当前不包含的内容

本文档当前不代表：

- 完整自动化 runner 已落地
- 完整 baseline 与 report 实例已生成
- 多 Provider 对比矩阵已实现
- CI 已自动执行回归

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "caseId|inputComposition|promptVersion|schemaVersion|rubricVersion|providerId|modelId|blocked|failed|available" evals docs/operations docs/contracts`

## 完成标准

满足以下条件时，可认为 `evals/` 已具备最小治理闭环：

- 团队知道什么时候必须跑回归
- 团队知道结果至少要记录哪些元数据
- README 不再把占位目录误写成已落地执行系统
- Prompt / Schema / Provider 变化不再脱离回归讨论
