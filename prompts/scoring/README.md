# `prompts/scoring`

## 子模块角色

该目录用于承载正式评分主线相关 Prompt 资产本体的目录入口。

## 当前仓库现实

当前 `prompts/scoring/` 下实际存在的目录只有：

- `rubric/`
- `templates/`
- `system/`

说明：

- 三者当前都还是占位目录
- `screening/` 与 `aggregation/` 作为规划中的阶段目录，当前尚未物理落地
- 因此这里的关键任务是先把目录边界写清，而不是假装正式 Prompt 资产已齐备

## 目录状态说明

### `rubric/`

- 当前最接近正式评分资产入口的阶段目录
- 后续如落地正式 Prompt 正文，优先从这里开始

### `templates/`

- 当前只应被理解为公共模板或片段占位目录
- 不是正式阶段真源
- 不得绕过 `registry/` 和 `versions/` 单独成为选择入口

### `system/`

- 当前仅保留为历史 / 占位目录
- 不是正式评分主线目录
- 不得把它重新升级为正式 Prompt 主线真源

## 正式评分结构约束

当前 Prompt 资产必须服从正式单主线方案：

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

但当前 Prompt-bearing 目录只预期优先覆盖：

- `input_screening`
- `rubric_evaluation`
- `aggregation`

说明：

- `consistency_check` 与 `final_projection` 当前默认不要求先建独立 Prompt 目录
- 这不意味着可以跳出正式五段主线

## 正式原则

- Prompt 资产本体只放在本目录及其正式子目录中
- 资产启用、版本绑定和适用范围由 `prompts/registry/` 与 `prompts/versions/` 承接
- 评分主线只保留 `pointwise`，不为 `pairwise` 维护正式 Prompt 分类
- 不得新增“多路径评分”“并行评分树”或“前端可选 Prompt”目录

## 当前不负责

- 维护版本记录
- 维护启用规则
- 定义正式 schema 字段
- 定义 API 状态语义
- 为不存在的阶段目录编造已落地资产

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "rubric|templates|system|pairwise|input_screening|aggregation" prompts/scoring/README.md prompts/README.md`

## DevFleet 使用约束

- Prompt 资产相关 mission 只能修改单一目录面
- 若要把 `screening/` 或 `aggregation/` 变成实际目录，必须连同 registry、version 和 evals 关系一起补齐
- 不得跨目录重写评分主线，也不得把 `system/` 当作默认正式目录
