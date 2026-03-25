# DevFleet Mission DAG

## 文档目的

本文档定义当前仓库面向 `/orchestrate` 与 `devfleet` 的 mission 依赖图、并行边界和禁止并行修改面。

它与 `docs/planning/devfleet-mission-catalog.md` 配套使用：

- `mission-catalog` 负责定义 mission 本身
- 本文档负责定义 mission 之间的 `depends_on`、波次顺序和并行规则

## 当前 DAG 作用域

当前 DAG 只覆盖 implementation-prep mission：

- `I1` 到 `I9`

当前不再下发文档修复 mission。

## Implementation-Prep DAG

### Wave 0：并行基础收口

可并行：

- `I1`：落地 `packages/schemas/evals/` 正式 schema
- `I2`：落地 `packages/provider-adapters/` 最小 provider port 与本地 adapter
- `I3`：落地 `packages/prompt-runtime/` registry / versions 读取接口

说明：

- 三者互不依赖，可并行启动
- 但不得并行改动 `packages/application/services/evaluation_service.py`

### Wave 1：Prompt 资产实例化

- `I4`：落地首批 Prompt registry / versions 实例与 scoring 资产骨架

依赖：

- `I3`

说明：

- `I4` 依赖 `I3` 提供的读取契约
- `I4` 不得反向修改 prompt runtime 接口本体

### Wave 2：application 去硬编码化

- `I5`：让 application service 通过 port 消费 prompt/provider

依赖：

- `I2`
- `I3`

说明：

- `I5` 是 API 与 worker 接线前的共同上游
- `I5` 完成前，不允许并行修改 `apps/api/src/api/` 与 `apps/worker/` 以接新依赖

### Wave 3：执行入口补齐

可并行：

- `I6`：收口 API 依赖注入与 DTO 对齐
- `I7`：落地 worker 最小执行入口
- `I8`：落地 evals runner 与报告输出

依赖：

- `I6` 依赖 `I5`
- `I7` 依赖 `I5`
- `I8` 依赖 `I1`、`I4`

说明：

- `I6` 与 `I7` 共用 application 新边界，但文件集不同，可以并行
- `I8` 主要收口 evals 闭环，可与 `I6`、`I7` 并行

### Wave 4：复审收尾

- `I9`：执行收口验证并复审 readiness

依赖：

- `I6`
- `I7`
- `I8`

说明：

- `I9` 只做结论与验证，不应重写上游对象边界

## 依赖矩阵

| Mission | depends_on |
| --- | --- |
| `I1` | 无 |
| `I2` | 无 |
| `I3` | 无 |
| `I4` | `I3` |
| `I5` | `I2`、`I3` |
| `I6` | `I5` |
| `I7` | `I5` |
| `I8` | `I1`、`I4` |
| `I9` | `I6`、`I7`、`I8` |

## 禁止并行修改面

以下修改面在同一波次内禁止被多个 mission 并行改动：

### 1. 正式 schema 真源

涉及文件：

- `packages/schemas/output/*.py`
- `packages/schemas/stages/*.py`
- `docs/contracts/canonical-schema-index.md`

原因：

- 这是 API、application、worker、evals 的共享结构基线
- `I1` 只能新增 `packages/schemas/evals/`，不得与其它 mission 并行重写既有 schema 子域

### 2. application 主用例边界

涉及文件：

- `packages/application/services/evaluation_service.py`
- `packages/application/ports/*.py`

原因：

- 这是 provider / prompt / API / worker 的共同接线中心
- `I5` 是该修改面的唯一 owner

### 3. API 资源语义与错误映射

涉及文件：

- `apps/api/src/api/*.py`
- `apps/api/contracts/*.md`

原因：

- `I6` 只能在既有资源语义下接新依赖
- 不允许 `I6` 与其它 mission 同时改 API 语义主文档

### 4. Prompt 治理与运行时绑定

涉及文件：

- `packages/prompt-runtime/**`
- `prompts/registry/**`
- `prompts/versions/**`
- `prompts/scoring/**`

原因：

- `I3` 负责接口，`I4` 负责实例
- 两者必须串行，避免接口与资产实例错位

### 5. Evals 运行闭环

涉及文件：

- `evals/runners/**`
- `evals/reports/**`
- `evals/baselines/**`

原因：

- `I8` 负责该修改面
- 不应让其它 mission 并行发明第二套报告输出口径

## 并行建议

### 可以并行

在满足 `depends_on` 后，以下修改面适合并行：

- `I1`、`I2`、`I3`
- `I6`、`I7`、`I8`

### 不适合并行

- 在 `I5` 未完成前并行修改 application、API、worker 的依赖接线
- 在 `I3` 未完成前并行落地 Prompt 资产实例与 runtime 接口
- 在 `I1` 未完成前并行让 runner 依赖尚不存在的 evals schema

## 合并顺序建议

当前 implementation-prep 阶段建议按以下顺序合并：

1. `I1`、`I2`、`I3`
2. `I4`
3. `I5`
4. `I6`、`I7`、`I8`
5. `I9`

## DevFleet 提交约束

在使用 `devfleet` 提交 mission 时，prompt 应至少要求每个 agent：

- 只改单一 mission 负责的文件集
- 只引用单一上游真源
- 只完成单一验收标准
- 不得顺手扩大到其它冻结面
- 不得把 README 占位内容误当正式真源或已实现能力
