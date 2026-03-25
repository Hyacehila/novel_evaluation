# `prompts/versions`

## 子模块角色

该目录用于记录 Prompt 版本信息、回滚关系与回归要求，是 Prompt 版本登记入口。

## 当前仓库现实

- 当前目录只有 README 级合同
- 还没有任何正式 version 记录实例文件
- 因此当前这里定义的是“版本记录最小格式”，而不是现成版本台账

## Prompt Version Record 最小字段

每条版本记录至少应包含：

- `promptId`
- `promptVersion`
- `status`
- `schemaVersion`
- `rubricVersion`
- `owner`
- `updatedAt`
- `changeSummary`
- `rollbackTarget`
- `evalRequirement`

## 字段说明

- `promptId`：稳定资产标识
- `promptVersion`：当前版本标识
- `status`：Prompt 生命周期状态，应与 `docs/prompting/prompt-lifecycle.md` 一致
- `rollbackTarget`：若需回退，应退回到的前一稳定版本；首版可为空
- `evalRequirement`：本次变更需要什么级别的回归说明
- `changeSummary`：本次变更为什么做，而不是只写“改了什么”

## 最小约束

- 不允许无版本记录直接替换正式 Prompt
- 版本记录必须能指出前一稳定点
- 版本变化若影响 Prompt 语义、schema 绑定、provider 范围或风险词表，必须附带回归要求

## 不负责

- 存放 Prompt 正文本体
- 决定运行时启用规则
- 定义正式结果字段结构
- 充当 registry 元数据目录

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "promptVersion|rollbackTarget|evalRequirement|changeSummary|status" prompts/versions/README.md docs/prompting/prompt-lifecycle.md prompts/README.md`

## DevFleet 使用约束

- 任何正式 Prompt 变更 mission 都必须同步更新版本记录实例或版本记录格式
- 在实例文件尚未落地前，不得宣称当前仓库已经具备可回滚的正式 Prompt 版本台账
