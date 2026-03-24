# `prompts/scoring`

该目录用于存放小说评分相关 Prompt 资产。

## 子目录职责

- `screening/`：输入预检查 Prompt
- `rubric/`：评分维度、评分标准、分点评价口径相关 Prompt
- `aggregation/`：聚合输出与最终结果口径相关 Prompt

## 原则

- 文件只承载 Prompt 资产本体
- 使用、加载、渲染与治理应由后端运行时负责
- 正式评分主线应围绕“预检查 → 分点评价 → 聚合输出”组织 Prompt 资产
- 评分人格、语气和输出风格约束，应并入对应阶段 Prompt 与 `prompts/registry/` 元数据，不再单独维护 `system/` 目录
