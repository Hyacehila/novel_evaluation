# Prompt 生命周期说明

## 文档目的

本文档冻结 `Phase 1` 的 Prompt 资产格式、目录规则、生命周期和运行时选择规则。

## 资产格式

- Prompt 正文固定为 `Markdown`
- registry 元数据固定为 `YAML`
- version 元数据固定为 `YAML`

## 正式目录

- `prompts/scoring/screening/{promptId}/{promptVersion}.md`
- `prompts/scoring/rubric/{promptId}/{promptVersion}.md`
- `prompts/scoring/aggregation/{promptId}/{promptVersion}.md`
- `prompts/registry/{promptId}.yaml`
- `prompts/versions/{promptId}/{promptVersion}.yaml`

说明：

- `screening/` 与 `aggregation/` 已升级为正式资产目录
- `system/` 与 `templates/` 不拥有正式选择权

## 生命周期

- `draft`
- `review`
- `candidate`
- `active`
- `deprecated`
- `retired`

## 最小元数据

### registry

- `promptId`
- `stage`
- `status`
- `schemaVersion`
- `rubricVersion`
- `inputCompositionScope`
- `evaluationModeScope`
- `providerScope`
- `modelScope`
- `enabled`

### version

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

## 运行时选择优先级

Prompt runtime 的正式选择优先级固定为：

`stage -> inputCompositionScope -> evaluationModeScope -> providerScope -> modelScope -> registry.status -> enabled`

其中：

- `registry.status` 仅允许 `candidate` 或 `active` 进入正式选择，并在同一 scope 层级候选中优先 `active`
- `version.status` 仅允许 `candidate` 或 `active` 进入正式加载，并优先 `active`
- 正文读取必须与选中的 `promptVersion` 一一绑定，不允许回退到无版本正文

## 治理规则

- Prompt 只能在后端治理
- Prompt 变更必须伴随 version 记录
- Prompt 进入 `candidate` 或 `active` 前必须绑定受控回归要求
- 运行时代码不得绕过 `prompts/` 目录长期内嵌正式 Prompt

## 非目标

- 前端持有 Prompt
- 多路径 Prompt 树
- 从运行时代码反向生成正式资产真源
