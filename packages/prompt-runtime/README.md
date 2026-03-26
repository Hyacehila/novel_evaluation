# `packages/prompt-runtime`

该模块承载 Prompt 运行时能力。

## 负责

- 读取 `prompts/scoring/**/*.md`
- 读取 `prompts/registry/*.yaml`
- 读取 `prompts/versions/**/*.yaml`
- 按冻结优先级选择 Prompt
- 向 application 返回 `promptId`、`promptVersion` 和正文内容

## 选择优先级

`registry.status -> stage -> inputCompositionScope -> evaluationModeScope -> providerScope -> modelScope -> enabled`

另外：

- `registry.status` 仅允许 `candidate` 或 `active`
- `version.status` 仅允许 `candidate` 或 `active`
- 正文读取路径固定绑定 `promptId + promptVersion`

## 不负责

- 存放 Prompt 正文真源
- 代替 registry/version 元数据
- 定义正式业务字段

## 目标输出

- `promptId`
- `promptVersion`
- `body`
- `schemaVersion`
- `rubricVersion`
