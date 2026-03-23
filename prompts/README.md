# `prompts`

该目录用于存放正式 Prompt 资产。

## 关键原则

- Prompt 只能在后端侧治理和使用
- Prompt 必须版本化、可追踪、可回滚
- Prompt 变更应与 Schema 和 Evals 一起管理
- 前端不得直接持有正式评分 Prompt

## 子目录建议

- `scoring/`：小说评分相关 Prompt
- `extraction/`：信息提取相关 Prompt
- `calibration/`：评分校准与一致性控制 Prompt
- `versions/`：版本登记与变更记录
- `registry/`：Prompt 元数据与启用规则
