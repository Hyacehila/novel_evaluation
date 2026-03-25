# `evals/reports`

## 子模块角色

该目录用于存放评测报告产物，是回归结果的结构化落点。

## 当前仓库现实

- 当前目录只有 README
- 还没有正式 report 实例文件
- 因此这里当前定义的是 report 最小信息要求，而不是现成报告仓

## Report 最小内容

每份正式报告至少应回答：

- 本次跑了哪些 `caseId`
- 使用了哪个 `promptVersion`
- 使用了哪个 `schemaVersion`
- 使用了哪个 `rubricVersion`
- 使用了哪个 `providerId` / `modelId`
- 结构合法性是否通过
- 与 baseline 相比发生了什么变化
- 哪些结果属于 `available`、`blocked`、`failed`

## 说明

- 代表性报告可选择纳入版本控制
- 本地运行中产生的临时报告应根据 `.gitignore` 规则处理
- 报告不能替代 baseline，也不能替代正式 schema

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "caseId|promptVersion|schemaVersion|rubricVersion|providerId|modelId|baseline|blocked|failed|available" evals/reports/README.md evals/README.md`

## DevFleet 使用约束

- report 相关 mission 必须明确报告输入、报告输出和比较对象
- 在实例文件尚未落地前，不得把 README 文本误写成“当前已有正式 report 产物”
