# DevFleet Mission Catalog

## 文档目的

本文档定义当前仓库面向 `/orchestrate` 与 `devfleet` 的正式 mission 清单。

本文档当前只列出**可以基于现有真源安全下发的窄 mission**，用于回答：

- 当前有哪些 mission 可以独立领取
- 每个 mission 应读取哪些真源文档与真实实现文件
- 每个 mission 应输出哪些资产
- 每个 mission 不允许越界修改哪些内容
- 每个 mission 应如何做最小验收

## 当前使用方式

当前 catalog 只包含 `I` 组：**implementation-prep mission**。

原因：

- 文档修复收口已完成
- 仓库当前已进入 `DevFleet-Ready`
- 但仍未达到 `Implementation-Ready`

## Mission 状态词表

- `active_now`：当前允许下发
- `blocked_by_impl`：被上游实现准备 mission 阻塞
- `future_only`：未来再使用

## 当前可下发的窄 mission

| Mission | 状态 | 目标 | 主要输入 | 主要输出 | depends_on | 并行建议 |
| --- | --- | --- | --- | --- | --- | --- |
| `I1` | `active_now` | 在 `packages/schemas/evals/` 落地正式 evals schema | `docs/contracts/canonical-schema-index.md`、`evals/*.md`、`packages/schemas/evals/README.md` | `EvalCase`、`EvalRecord`、`EvalBaseline`、`EvalReport` 正式 schema 类 | 无 | 可作为起点 |
| `I2` | `active_now` | 在 `packages/provider-adapters/` 落地最小 provider port 与本地 adapter | `packages/provider-adapters/README.md`、`docs/architecture/provider-abstraction.md`、`packages/application/services/evaluation_service.py` | provider port、占位 adapter、错误映射边界 | 无 | 可与 `I1`、`I3` 并行 |
| `I3` | `active_now` | 在 `packages/prompt-runtime/` 落地 registry / versions 读取接口 | `packages/prompt-runtime/README.md`、`prompts/registry/README.md`、`prompts/versions/README.md` | prompt runtime port、registry 读取器、version 读取器 | 无 | 可与 `I1`、`I2` 并行 |
| `I4` | `active_now` | 落地首批 Prompt registry / versions 实例与 scoring 资产骨架 | `prompts/*.md`、`docs/prompting/prompt-lifecycle.md` | 可被运行时读取的最小元数据实例和正式资产骨架 | `I3` | 串行接在 `I3` 后 |
| `I5` | `blocked_by_impl` | 让 application service 通过 port 消费 prompt/provider | `packages/application/services/evaluation_service.py`、`packages/application/README.md`、`I2`、`I3` 产物 | 去硬编码化的 application service | `I2`、`I3` | 串行 |
| `I6` | `blocked_by_impl` | 收口 API 依赖注入与 DTO 对齐 | `apps/api/src/api/*.py`、`apps/api/contracts/*.md`、`I5` 产物 | API 依赖接线、DTO 对齐、测试更新 | `I5` | 串行 |
| `I7` | `blocked_by_impl` | 在 `apps/worker/` 落地最小执行入口 | `apps/worker/README.md`、`packages/application/README.md`、`I5` 产物 | worker 执行入口与最小验收命令 | `I5` | 可与 `I8` 并行 |
| `I8` | `blocked_by_impl` | 在 `evals/runners/` 落地最小本地 runner 与报告输出 | `evals/runners/README.md`、`evals/reports/README.md`、`I1`、`I4` 产物 | 本地 runner、报告写出入口、基线比较骨架 | `I1`、`I4` | 可与 `I7` 并行 |
| `I9` | `blocked_by_impl` | 执行收口验证并复审 readiness | `I1-I8` 产物、`docs/operations/quality-gates-and-regression.md` | `Implementation-Ready / Not Yet` 结论与剩余阻塞项 | `I6`、`I7`、`I8` | 收尾串行 |

## Mission 详细说明

### `I1` 在 `packages/schemas/evals/` 落地正式 evals schema

- **目标**：把 `EvalCase / EvalRecord / EvalBaseline / EvalReport` 从文档对象变成正式 schema 类
- **输入真源文档**：
  - `docs/contracts/canonical-schema-index.md`
  - `evals/README.md`
  - `evals/datasets/README.md`
  - `evals/runners/README.md`
  - `evals/cases/README.md`
  - `evals/baselines/README.md`
  - `evals/reports/README.md`
- **输出资产**：
  - `packages/schemas/evals/*.py`
  - `packages/schemas/evals/__init__.py`
- **不做什么**：
  - 不实现 runner
  - 不改 API 状态语义
- **验收标准**：
  - schema 类与文档对象一一对应
  - `canonical-schema-index.md` 不再把 evals 对象标为 `schema_pending`
- **验证命令**：
  - `uv run python -m compileall packages/schemas`
- **禁止修改面**：
  - 不得重写 `packages/schemas/output/` 与 `packages/schemas/stages/` 已冻结对象

### `I2` 在 `packages/provider-adapters/` 落地最小 provider port 与本地 adapter

- **目标**：给 application 层提供最小 provider 抽象，而不是继续使用内嵌常量
- **输入真源文档**：
  - `packages/provider-adapters/README.md`
  - `docs/architecture/provider-abstraction.md`
  - `docs/operations/rollback-and-fallback.md`
- **真实实现参考**：
  - `packages/application/services/evaluation_service.py`
- **输出资产**：
  - provider port
  - 本地占位 adapter
  - 错误映射说明或类型
- **不做什么**：
  - 不接入正式远端 provider
  - 不在 application 层外泄 SDK 细节
- **验收标准**：
  - application 可依赖抽象而非 provider 常量命名
- **验证命令**：
  - `uv run python -m compileall packages/provider-adapters packages/application`
- **禁止修改面**：
  - 不得改动正式任务状态、结果状态与错误码集合

### `I3` 在 `packages/prompt-runtime/` 落地 registry / versions 读取接口

- **目标**：让 Prompt 资产治理从 README 进入可被 application 消费的最小运行时接口
- **输入真源文档**：
  - `packages/prompt-runtime/README.md`
  - `prompts/registry/README.md`
  - `prompts/versions/README.md`
  - `prompts/scoring/README.md`
- **输出资产**：
  - prompt runtime port
  - registry 读取器
  - versions 读取器
- **不做什么**：
  - 不实现复杂模板渲染系统
  - 不发明第二套 Prompt 真源
- **验收标准**：
  - runtime 能明确回答“读取哪个 promptId / promptVersion / stage”
- **验证命令**：
  - `uv run python -m compileall packages/prompt-runtime`
- **禁止修改面**：
  - 不得把 `prompts/scoring/system/` 重新升级为正式真源

### `I4` 落地首批 Prompt registry / versions 实例与 scoring 资产骨架

- **目标**：给 `I3` 提供可真实读取的最小 Prompt 资产实例
- **输入真源文档**：
  - `prompts/README.md`
  - `prompts/scoring/README.md`
  - `prompts/registry/README.md`
  - `prompts/versions/README.md`
- **输出资产**：
  - 首批 registry 元数据实例
  - 首批版本记录实例
  - 与当前主线一致的 scoring 资产骨架
- **不做什么**：
  - 不编写完整业务 Prompt 大全集
  - 不新增非正式 Prompt 分类
- **验收标准**：
  - `I3` 的读取接口能成功解析最小实例
- **验证命令**：
  - `git diff --check`
- **禁止修改面**：
  - 不得让 `templates/`、`system/` 占位目录成为新真源

### `I5` 让 application service 通过 port 消费 prompt/provider

- **目标**：把当前 application service 中的硬编码 provider / prompt 元信息抽离到依赖边界
- **输入真源文档**：
  - `packages/application/README.md`
  - `docs/architecture/application-layer-boundaries.md`
  - `I2`、`I3` 产物
- **真实实现参考**：
  - `packages/application/services/evaluation_service.py`
- **输出资产**：
  - 去硬编码化的 application service
  - 必要的 port 连接与测试调整
- **不做什么**：
  - 不扩写多条评分主线
  - 不引入数据库或消息队列
- **验收标准**：
  - service 不再直接写死 `provider-local` / `model-local` / prompt 常量
- **验证命令**：
  - `uv run pytest apps/api/tests/test_application.py apps/api/tests/test_schemas.py`
- **禁止修改面**：
  - 不得修改既有状态组合规则

### `I6` 收口 API 依赖注入与 DTO 对齐

- **目标**：让 `apps/api/` 通过明确依赖注入接入 application / prompt / provider 边界
- **输入真源文档**：
  - `apps/api/contracts/api-v0-overview.md`
  - `apps/api/contracts/job-lifecycle-and-error-semantics.md`
  - `docs/contracts/frontend-minimal-api-assumptions.md`
- **真实实现参考**：
  - `apps/api/src/api/*.py`
  - `apps/api/tests/test_api.py`
- **输出资产**：
  - 对齐后的 API 接线与测试
- **不做什么**：
  - 不新增对外 API 路由
  - 不改动已冻结 DTO 语义
- **验收标准**：
  - 现有 API 路由在新依赖接线下仍保持相同资源语义
- **验证命令**：
  - `uv run pytest apps/api/tests/test_api.py`
- **禁止修改面**：
  - 不得重写 API 契约主文档语义

### `I7` 在 `apps/worker/` 落地最小执行入口

- **目标**：让 worker 从 README 边界进入最小可执行入口
- **输入真源文档**：
  - `apps/worker/README.md`
  - `docs/operations/local-development-topology.md`
  - `docs/operations/rollback-and-fallback.md`
- **输出资产**：
  - worker 最小执行入口
- **不做什么**：
  - 不实现复杂调度系统
  - 不发明新的任务状态
- **验收标准**：
  - 本地存在一个终止型 worker 执行入口
- **验证命令**：
  - `uv run python -m compileall apps/worker`
- **禁止修改面**：
  - 不得改写 `completed + blocked` / `failed + not_available` 边界

### `I8` 在 `evals/runners/` 落地最小本地 runner 与报告输出

- **目标**：给 evals 体系补上最小执行闭环
- **输入真源文档**：
  - `evals/README.md`
  - `evals/datasets/README.md`
  - `evals/runners/README.md`
  - `evals/reports/README.md`
- **输出资产**：
  - 本地 runner
  - 报告输出骨架
  - 基线比较骨架
- **不做什么**：
  - 不实现复杂统计仪表盘
  - 不要求 CI 集成先完成
- **验收标准**：
  - runner 可在有限时间内输出至少一份结构化报告骨架
- **验证命令**：
  - `uv run python -m compileall evals`
- **禁止修改面**：
  - 不得在 evals 中反向定义正式业务结果字段

### `I9` 执行收口验证并复审 readiness

- **目标**：输出当前仓库是否达到 `Implementation-Ready`
- **输入真源文档**：
  - `I1-I8` 全部产物
  - `docs/operations/quality-gates-and-regression.md`
  - `docs/planning/layered-rubric-implementation-plan.md`
- **输出资产**：
  - `Implementation-Ready / Not Yet` 结论
  - 剩余阻塞项清单
- **不做什么**：
  - 不借复审之名重写字段真源
- **验收标准**：
  - 能明确回答“现在是否可以从 implementation-prep 进入实际实现波次”
- **验证命令**：
  - 以 `quality-gates-and-regression.md` 中适用命令为准
- **禁止修改面**：
  - 不得把 `DevFleet-Ready` 与 `Implementation-Ready` 混为同一层

## 下发规则

- 当前只允许下发 `I1-I4`
- `I5-I9` 必须等待各自上游完成后才能激活
- 任何 mission 都必须遵守“单一上游真源、单一验收标准、单一文件集”原则
- 任何 mission 都不得把 README 占位内容误写成已实现运行时能力
