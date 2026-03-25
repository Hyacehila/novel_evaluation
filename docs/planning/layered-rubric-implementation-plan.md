# 面向网络小说联合投稿包全 LLM Rubric 主线的 DevFleet 实施计划

## 文档目的

本文档是当前仓库进入 `/orchestrate` 与 `devfleet` 前的总计划入口。

它回答四个问题：

- 当前仓库处于哪一个 readiness 层级
- 当前哪些结构真源已经真实落地
- 后续 implementation mission 应如何按窄任务拆分
- 在进入实现阶段前，哪些边界仍然不能被跳过

本文档当前用于**文档收口后的实施准备**，不授权无边界并行开发。

## Readiness 分层

### 1. `Doc-Ready`

表示核心架构、范围、术语、状态语义和目录边界已经可独立理解。

### 2. `DevFleet-Ready`

表示仓库已经具备以下条件：

- 关键文档有明确真源
- mission 已可拆成单文件集、单验收标准的窄任务
- mission 之间存在明确 `depends_on` DAG
- 每个 mission 都有边界、非目标、验收标准和终止型验证入口
- 并行与串行边界已经写清楚

### 3. `Implementation-Ready`

表示除了满足 `DevFleet-Ready` 外，还额外满足：

- 剩余关键运行时占位已经收口为可执行模块
- Prompt runtime、provider adapter、worker、evals runner 具备最小执行闭环
- 模块 I/O 契约已能直接指导代码落位
- 运行时实现不再依赖大面积占位常量或 README 解释补洞

## 当前判断

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Not Yet`

## 当前仓库基线

当前已确认的真实基线如下：

### 已落地的正式结构与最小实现

- `packages/schemas/` 已落地 `common/`、`input/`、`output/`、`stages/` 正式 schema 类
- `packages/application/` 已落地最小 `EvaluationService`、`TaskRepository` port 与本地内存实现
- `apps/api/` 已落地 `FastAPI` 应用、路由、错误映射和测试基线
- `apps/api/tests/` 已覆盖 schema、application 与 API 最小语义

### 仍处于文档/占位阶段的面

- `packages/schemas/evals/` 仍只有 `README.md`，正式 schema 类尚未落地
- `packages/provider-adapters/` 仍处于合同文档阶段
- `packages/prompt-runtime/` 仍处于合同文档阶段
- `apps/worker/` 仍处于合同文档阶段
- `evals/runners/` 与 `evals/reports/` 仍处于治理文档阶段
- `prompts/` 目前主要是治理文档与占位目录，尚未形成可执行资产闭环

### 当前实现中的占位约束

- `packages/application/services/evaluation_service.py` 当前仍使用 `provider-local` / `model-local` 和固定版本常量作为本地占位基线
- 这说明仓库已经具备最小工程基线，但尚未进入正式 provider / prompt runtime / worker 闭环

## 当前阻塞 `Implementation-Ready` 的剩余项

当前阻塞的不是文档真源，而是剩余运行时空位：

- `packages/schemas/evals/` 正式对象尚未落地
- provider adapter 尚未以代码方式收口
- prompt runtime 尚未以代码方式收口
- application service 尚未去除对本地占位 provider / prompt 常量的直接依赖
- worker 执行入口尚未落地
- evals runner 与报告写出入口尚未落地
- `prompts/` 仍缺少与 registry / versions 绑定的首批正式资产实例

## 当前阶段目标

当前阶段只做两件事：

- 维持文档真源稳定
- 在文档真源基础上按窄 mission 推进 implementation-prep

这意味着当前阶段**不允许**：

- 跳过 `mission-catalog` 与 `mission-dag` 直接发起大任务
- 把 README 占位解释为已实现运行时能力
- 在 schema / 状态 / Prompt 真源未指明时跨模块同时开工
- 引入 `pairwise`、额外评分分支或多路径正式主线

## 文档真源层级

当前阶段统一采用以下真源优先级：

1. 已落地的 `packages/schemas/**/*.py`
2. `docs/contracts/canonical-schema-index.md`
3. `docs/contracts/rubric-stage-contracts.md`
4. `docs/contracts/json-contracts.md`
5. `apps/api/contracts/api-v0-overview.md` 与 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
6. `docs/planning/devfleet-mission-catalog.md` 与 `docs/planning/devfleet-mission-dag.md`
7. `docs/operations/quality-gates-and-regression.md` 与 `docs/operations/rollback-and-fallback.md`

说明：

- 已落地的 schema 类优先级高于所有文档说明
- 对尚未落地的对象，`canonical-schema-index.md` 是唯一对象级索引真源
- 前端假契约、API DTO 文档、README 和 Evals 文档都不得反向成为正式字段真源

## 当前允许下发的任务类型

当前允许下发的是**窄实现准备 mission**，特点必须同时满足：

- 单一文件集
- 单一上游真源
- 单一非目标边界
- 单一终止型验收入口

正式任务拆分与顺序以：

- `docs/planning/devfleet-mission-catalog.md`
- `docs/planning/devfleet-mission-dag.md`

为准。

## 当前推荐的下发顺序

### Wave 1：并行收口基础运行时空位

- `I1`：落地 `packages/schemas/evals/` 正式 schema
- `I2`：落地 `packages/provider-adapters/` provider port 与本地占位 adapter
- `I3`：落地 `packages/prompt-runtime/` registry / versions 读取能力
- `I4`：落地首批 Prompt registry / versions 实例与 scoring 资产骨架

### Wave 2：让 application 去硬编码化

- `I5`：让 `packages/application/` 通过 port 消费 prompt/provider，而不是直接使用本地常量

### Wave 3：补齐执行入口

- `I6`：落地 `apps/api/` 依赖注入与 DTO 对齐收口
- `I7`：落地 `apps/worker/` 最小执行入口
- `I8`：落地 `evals/runners/` 最小本地 runner 与报告输出

### Wave 4：统一验收

- `I9`：执行收口验证并复审 readiness

## 进入 `Implementation-Ready` 的判断门槛

满足以下条件时，可判定仓库达到 `Implementation-Ready`：

- `packages/schemas/evals/` 已有正式 schema 类
- provider adapter 与 prompt runtime 已有最小代码闭环
- application service 不再直接写死占位 provider / prompt 元信息
- worker 与 evals runner 至少各有一个终止型本地执行入口
- Prompt 资产、registry、versions 与运行时加载逻辑已经绑定
- API / application / worker / evals 的最小验证命令可实际执行并通过

## 当前仍明确不做

- 不在当前阶段引入公网鉴权、多租户和复杂部署前提
- 不把本地占位 provider 误写成正式多 provider 策略
- 不把研究目录或 README 文本当成运行时代码能力
- 不在 `Implementation-Ready` 之前启动无依赖约束的并行改造

## 完成后预期结论

当前文档收口完成后，仓库的正确结论应是：

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Not Yet`

这意味着：

- 可以安全进入 mission DAG
- 可以开始下发窄 implementation-prep mission
- 但不能跳过 DAG 直接展开大规模业务实现
