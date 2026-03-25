# `prompts`

该目录承载正式 Prompt 资产真源。

## 冻结结论

- Prompt 正文固定为 `Markdown`
- 元数据固定为 `YAML`
- 正式评分资产只在 `prompts/scoring/`
- `screening/`、`rubric/`、`aggregation/` 都是正式资产目录

## 目录结构

- `prompts/scoring/`：评分主线正文资产
- `prompts/registry/`：按 `promptId` 维护 registry 元数据
- `prompts/versions/`：按 `promptId/promptVersion` 维护版本元数据
- `prompts/extraction/`、`prompts/calibration/`：保留目录，不属于当前正式主线

## 当前原则

- 前端不得持有正式 Prompt
- `packages/prompt-runtime/` 只负责读取和选择，不反向定义资产
- `system/`、`templates/` 不得被重新升级为正式主线真源
