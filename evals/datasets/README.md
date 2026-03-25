# `evals/datasets`

## 子模块角色

该目录用于放置评测样本、金标准和测试夹具，是回归体系的输入合同入口。

## 当前仓库现实

当前目录下实际存在：

- `samples/`
- `goldens/`
- `fixtures/`

但仍只有 `.gitkeep` 占位，没有正式样本实例文件。

## Dataset Contract

每个正式可消费的数据集项至少应回答：

- `caseId` 是什么
- 样本用途是什么
- `inputComposition` 是什么
- 是否进入 baseline
- 期望结果类型是什么
- 关联的 `promptVersion` / `schemaVersion` / `rubricVersion` 范围是什么

## 最小字段建议

- `caseId`
- `title`
- `inputComposition`
- `chaptersRef` 或 `chaptersContent`
- `outlineRef` 或 `outlineContent`
- `tags`
- `expectedOutcomeType`
- `includedInBaseline`
- `notes`

## 样本分类要求

当前至少应覆盖：

- 强正文 + 强大纲
- 强正文 + 弱大纲
- 弱正文 + 强大纲
- 跨输入冲突
- 单侧输入降级
- 风险样本
- 回归关注样本

## 不负责

- 定义正式结果字段真源
- 代替 runner 执行逻辑
- 代替报告结构定义
- 把研究样本直接包装成正式结果实例

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "caseId|inputComposition|includedInBaseline|expectedOutcomeType|promptVersion|schemaVersion|rubricVersion" evals/datasets/README.md evals/README.md`

## DevFleet 使用约束

- 数据集相关 mission 必须明确修改的是样本、金标准还是夹具
- 在实例文件尚未落地前，不得把 README 描述误写成“当前已存在正式样本集”
- 不得在数据集 README 中反向定义正式结果字段结构
