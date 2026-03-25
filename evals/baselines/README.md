# `evals/baselines`

## 子模块角色

该目录用于存放历史评测基线与对比基准，是回归比较的稳定参考入口。

## 当前仓库现实

- 当前目录只有 README
- 还没有正式 baseline 实例文件
- 因此这里当前定义的是 baseline 最小记录合同，而不是现成基线台账

## Baseline Record 最小字段

每条 baseline 记录至少应包含：

- `baselineId`
- `caseId` 或 case 集合引用
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 记录时间
- 对比结论摘要
- 是否可作为当前稳定参考

## 目标

- 为回归比较提供稳定参考
- 为 Prompt / Schema / Provider 变更提供可追踪基准
- 避免“新结果直接覆盖旧基线”

## 不负责

- 代替报告产物目录
- 代替正式 schema 定义
- 代替 runner 执行逻辑

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "baselineId|promptVersion|schemaVersion|rubricVersion|providerId|modelId|稳定参考" evals/baselines/README.md evals/README.md`

## DevFleet 使用约束

- baseline 相关 mission 必须明确是“新增基线”“更新基线”还是“废弃基线”
- 在实例文件尚未落地前，不得把 README 文本误写成“当前已有正式 baseline 台账”
