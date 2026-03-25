# `prompts/registry`

## 子模块角色

该目录用于记录 Prompt 资产的元信息、启用规则与适用范围，是运行时选择 Prompt 的治理入口。

## 当前仓库现实

- 当前目录只有 README 级合同
- 还没有具体的 registry 元数据实例文件
- 因此当前这里定义的是“实例应长成什么样”，而不是“当前已经有哪些 Prompt 被启用”

## Prompt Registry Metadata 最小字段

每条 registry 元数据至少应包含：

- `promptId`
- `promptVersion`
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

## 字段说明

- `stage`：当前只允许使用正式主线中的 Prompt-bearing 阶段名：
  - `input_screening`
  - `rubric_evaluation`
  - `aggregation`
- `status`：Prompt 生命周期状态，具体约束与 `docs/prompting/prompt-lifecycle.md` 保持一致
- `inputCompositionScope`：适用输入组成范围
- `evaluationModeScope`：适用的 `full` / `degraded` 范围
- `providerScope` / `modelScope`：适用模型范围
- `enabled`：当前是否允许被运行时选择

说明：

- 若未来 `consistency_check` 或 `final_projection` 需要独立 Prompt 选择，必须先更新上游治理文档，不得直接私自发明新取值
- 不允许继续使用 `screening` / `rubric_scoring` 这类与正式阶段枚举不一致的旧命名

## 作用边界

- 记录启用规则与适用范围
- 记录 Prompt 与 schema / rubric / provider 的绑定关系
- 为 `packages/prompt-runtime/` 提供选择依据
- 不承载 Prompt 正文本体

## 不负责

- 决定领域对象语义
- 定义正式结果结构
- 替代运行时本身
- 反向定义前端可见的 Prompt 选择逻辑

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "promptId|promptVersion|input_screening|rubric_evaluation|aggregation|enabled|inputCompositionScope|evaluationModeScope" prompts/registry/README.md prompts/README.md docs/prompting/prompt-lifecycle.md`

## DevFleet 使用约束

- registry 相关 mission 必须明确修改的是字段格式、启用规则还是绑定关系
- 在实例文件尚未落地前，不得把 README 文本误当作当前活跃 Prompt 列表
- 不得在 registry 中重新定义正式 schema 字段或评分主线
