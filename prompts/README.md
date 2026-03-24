# `prompts`

该目录用于存放正式 Prompt 资产。

## 关键原则

- Prompt 只能在后端侧治理和使用
- Prompt 必须版本化、可追踪、可回滚
- Prompt 变更应与 Schema 和 Evals 一起管理
- 前端不得直接持有正式评分 Prompt
- `packages/prompt-runtime` 负责读取和渲染 Prompt，但 Prompt 治理真源仍在本目录

## 子目录建议

- `scoring/`：小说评分相关 Prompt
- `versions/`：版本登记与变更记录
- `registry/`：Prompt 元数据、启用规则与映射关系

## 评分主线建议目录

- `scoring/screening/`：输入预检查 Prompt
- `scoring/rubric/`：分点评价 Prompt
- `scoring/aggregation/`：聚合输出 Prompt

## 说明

- 评分主线当前围绕“预检查 → 分点评价 → 聚合输出”组织 Prompt 资产
- 需要跨阶段共享的启用规则、风格约束和版本绑定信息，应收敛到 `registry/` 与 `versions/`
- 不再额外维护独立的 `scoring/system/` 正式目录，避免 Prompt 分类真源分裂
