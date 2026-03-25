# `prompts/registry`

该目录用于维护按 `promptId` 划分的 registry 元数据。

## 文件格式

- 文件路径：`prompts/registry/{promptId}.yaml`
- 文件格式：`YAML`

## 最小字段

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
- `notes`

## 规则

- `stage` 只能使用正式阶段名
- registry 只描述启用与适用范围
- registry 不承载 Prompt 正文
