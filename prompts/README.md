# `prompts`

## 目录角色

该目录用于承载正式 Prompt 资产治理信息与后续 Prompt 正文资产。

Prompt 真源只能由后端治理；前端不得直接持有、拼接或选择正式评分 Prompt。

## 当前仓库现实

当前仓库在 `prompts/` 下已经存在：

- `scoring/`
- `registry/`
- `versions/`
- `extraction/`
- `calibration/`

但当前已落地内容仍以 README 与 `.gitkeep` 占位为主：

- 尚未落地正式 Prompt 正文实例
- 尚未落地 `registry` 元数据实例
- 尚未落地 `versions` 版本记录实例

因此当前 `prompts/` 的状态是：

- Prompt 治理合同已冻结
- Prompt 资产实例仍待后续窄 mission 落地

## 正式原则

- Prompt 只能在后端治理和使用
- Prompt 变更必须与 Schema、Evals 和回归要求一起考虑
- Prompt 的使用真源在本目录，不在 `packages/prompt-runtime/`
- `packages/prompt-runtime/` 只负责读取、选择和渲染，不负责反向定义资产真源
- 不允许前端持有正式评分 Prompt 正文

## 当前目录解释

### `scoring/`

- 正式评分主线的 Prompt 资产入口
- 当前内部只有占位目录和 README

### `registry/`

- Prompt 元数据、启用规则和适用范围入口
- 当前为 README 级合同，实例文件待落地

### `versions/`

- Prompt 版本记录、回滚关系与回归要求入口
- 当前为 README 级合同，实例文件待落地

### `extraction/` / `calibration/`

- 当前仓库中仅为占位目录
- 不是当前正式评分主线真源
- 若未来要吸收进正式主线，必须先补齐 registry、version 与 evals 关系，而不是直接升级为正式目录

## 正式评分主线约束

Prompt 治理必须服从当前单主线正式方案：

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

说明：

- Prompt 资产目录不要求与五段主线一一对应地提前全部物理落地
- 但不能借此复活旧的多路径、`pairwise` 或前端持有 Prompt 的做法

## 明确不采用

首期明确不采用：

- `pairwise` 正式评分 Prompt 分类
- 多路径评分 Prompt 树
- 前端定义 Prompt 选择逻辑
- 从运行时代码反向生成 Prompt 真源
- 通过 `system/`、`templates/`、研究目录偷偷升级第二套主线

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "scoring|registry|versions|extraction|calibration|pairwise|前端" prompts/README.md prompts/scoring/README.md prompts/registry/README.md prompts/versions/README.md`

## DevFleet 使用约束

- Prompt 相关 mission 必须明确修改的是哪一层：资产、registry、version、还是回归要求
- 在实例文件尚未落地前，不得把 README 文本误写成“当前已有正式 Prompt 内容”
- Prompt 相关 mission 不得顺手引入第二套阶段命名或评分主线
