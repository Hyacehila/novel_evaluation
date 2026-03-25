# `prompts/versions`

该目录用于维护 Prompt 版本记录。

## 文件格式

- 文件路径：`prompts/versions/{promptId}/{promptVersion}.yaml`
- 文件格式：`YAML`

## 最小字段

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

## 规则

- 不允许无版本记录直接替换正式 Prompt
- 版本记录必须指向可回退目标
- `evalRequirement` 必须能触发一次受控回归
