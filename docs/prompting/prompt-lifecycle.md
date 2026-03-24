# Prompt 生命周期说明

## 文档目的

本文档定义正式 Prompt 资产在项目中的生命周期、命名规则、版本规则、发布与回滚原则，用于让 `prompts/` 从目录骨架演进为可治理资产体系。

本文档回答的问题是：

- Prompt 如何分类
- Prompt 文件如何命名与组织
- Prompt 版本如何标识
- Prompt 从草案到正式上线要经历什么阶段
- Prompt 与 Schema、Evals、运行时如何绑定

本文档不负责：

- 编写具体 Prompt 正文
- 定义 `rubric` 策略细节
- 替代正式运行时实现

## 核心原则

- Prompt 只能在后端侧治理和使用
- Prompt 必须版本化、可追踪、可回滚
- Prompt 修改必须与 Schema 和 Evals 联动
- 前端不得持有正式 Prompt 正文
- 运行时代码不得绕过正式资产目录直接内嵌长期 Prompt

## Prompt 资产分类

从治理视角，建议将正式 Prompt 资产至少划分为：

- `prompts/scoring/screening/`
- `prompts/scoring/rubric/`
- `prompts/scoring/aggregation/`
- `prompts/versions/`
- `prompts/registry/`

### 分类说明

- `screening/`：输入预检查相关资产
- `rubric/`：分点评价相关资产
- `aggregation/`：聚合输出相关资产
- `versions/`：版本记录与变更登记
- `registry/`：元数据、启用规则与映射关系

## 命名与目录规则

### 基本要求

- 命名应稳定且语义清晰
- 不使用临时实验命名作为长期正式名
- 不让多个目录重复维护同一正式 Prompt 本体

### 推荐内容组织

一个正式 Prompt 资产至少需要可关联：

- `promptId`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- 适用阶段或适用用例

## 版本标识规则

### 最小要求

每个正式 Prompt 都应具备：

- 唯一标识
- 版本标识
- 与结果结构的绑定信息

### 推荐原则

- 破坏性 Prompt 改动应显式升级版本
- 会影响输出结构、结果语义、执行阶段的调整不得视为“无影响改动”
- 小修正也应留下版本记录

## 生命周期阶段

建议将正式 Prompt 生命周期划分为以下阶段：

### 1. 草案 `draft`

含义：

- 已形成可讨论内容
- 尚未进入正式可用状态

### 2. 评审中 `review`

含义：

- 已进入团队评审
- 正在核对其目标、结构依赖和适用范围

### 3. 试运行 `candidate`

含义：

- 可以进入受控验证
- 可在有限样本上参与 Evals

### 4. 正式 `active`

含义：

- 已通过当前阶段验收
- 可作为正式运行时可选资产

### 5. 废弃 `deprecated`

含义：

- 不再推荐用于新任务
- 仅用于追溯、兼容或历史比对

### 6. 停用 `retired`

含义：

- 不再参与正式运行
- 保留历史记录但不继续启用

## Prompt 与 Schema 的绑定关系

每个正式 Prompt 都应声明：

- 目标输出结构类型
- 目标 `schemaVersion`
- 是否面向正式结果对象或中间阶段对象

约束：

- Prompt 不得在目标结构未定义时长期处于“默认正式状态”
- 如果 Prompt 变更导致结构输出变化，应触发 Schema 兼容性评估

## Prompt 与 Evals 的绑定关系

每个进入 `candidate` 或 `active` 的 Prompt 都应具备：

- 可用于评测的样本范围说明
- 与基线比较的方式说明
- 回滚判断依据

说明：

- 没有 Evals 约束的 Prompt，不能视为长期正式资产

## Prompt 与运行时的关系

运行时只负责：

- 选择 Prompt
- 读取 Prompt
- 渲染 Prompt
- 记录 Prompt 版本元信息

运行时不应：

- 成为 Prompt 正文真源
- 直接在代码里长期保留未版本化 Prompt
- 绕过资产目录私自替换正式 Prompt

## 修改流程

推荐流程：

1. 提出修改需求
2. 判断影响范围
3. 更新 Prompt 资产与版本记录
4. 检查 Schema 绑定
5. 检查 Evals 是否需要更新
6. 完成评审后进入 `candidate` 或 `active`

## 回滚策略

Prompt 回滚必须具备：

- 明确的前一版本引用
- 回滚原因说明
- 与 Schema/Evals 的兼容性说明

约束：

- 不允许以“直接覆盖文件”替代回滚记录

## 禁止事项

以下做法禁止作为正式治理方式：

- 前端持有正式 Prompt 正文
- 在 API 层直接拼长期 Prompt
- 未版本化直接替换正式 Prompt
- Prompt 与 Schema 脱钩演进
- Prompt 修改后不更新版本记录

## 最小元数据建议

每个正式 Prompt 至少应可追踪以下信息：

- `promptId`
- `promptVersion`
- `status`
- `schemaVersion`
- `rubricVersion`
- `owner`
- `updatedAt`
- `notes`

## Phase 1 最小治理要求

在 `Phase 1` 中，至少应做到：

- 正式 Prompt 资产目录边界清晰
- Prompt 生命周期阶段清晰
- Prompt 与 Schema / Evals 的依赖关系明确
- 后端实现不得绕过正式资产治理

## 完成标准

满足以下条件时，可认为 Prompt 生命周期文档已足以支撑开发：

- 团队知道 Prompt 从草案到正式的流转方式
- 团队知道 Prompt 修改后需要同步哪些资产
- 运行时实现不会自然演化成 Prompt 真源
- 前端与后端的 Prompt 责任边界清晰

## 与现有文档的关系

- Prompt 目录定位见 `prompts/README.md`
- 阶段契约见 `docs/contracts/rubric-stage-contracts.md`
- Schema 治理见 `docs/contracts/schema-versioning-policy.md`
- 应用层边界见 `docs/architecture/application-layer-boundaries.md`
