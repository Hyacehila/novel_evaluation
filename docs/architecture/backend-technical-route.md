# 后端技术路线

## 文档定位

本文用于在现有后端边界、API 契约、Prompt 治理与 Schema 治理文档基础上，冻结 `apps/api` 与相关后端模块的实现基线。

本文回答“后端用什么技术实现、按什么实现策略落地”，但不替代 API v0 契约、任务状态机、正式 Schema 或 Prompt 正文设计。

## 技术路线结论

当前后端实现基线确定为：

- 语言与运行基线：`Python 3.13 + uv`
- Web API 框架：`FastAPI`
- 边界校验与 DTO 表达：`Pydantic`
- LLM Provider：`DeepSeek API`
- LLM 编排框架：`PocketFlow`
- 部署定位：开源项目，本地部署、本机启动、前后端协同运行
- 运行方式：`apps/api` 作为主接口入口，`apps/worker` 承担异步执行与回归入口

## 为什么采用这条路线

### 1. 最适合当前项目阶段

当前项目已经冻结了 API 契约、任务状态语义、Prompt 生命周期、Schema 治理与正式评分主线。后端当前最需要的不是继续维持技术中立，而是选择一套足够稳定、足够轻量、足够清晰的实现基线，把这些文档约束真正承接起来。

`FastAPI + Pydantic + PocketFlow` 的组合，适合把“接口边界”“结构校验”“LLM 多阶段编排”分开落位，同时又不会引入过重的工程负担。

### 2. 最适合本地部署与开源使用模式

本项目当前的目标不是提供公网高并发托管服务，而是让用户能够在自己的电脑上拉起前端与后端，配置 API Key 后直接使用。

在这种前提下，后端优先考虑：

- 启动成本低
- 本地运行简单
- 调试路径直接
- 文档与代码映射清晰
- 对单机资源约束友好

因此当前不以复杂分布式架构、过重的中间件体系或 SaaS 化部署假设作为前提。

### 3. 最适合正式评分主线

当前正式评分主线已经冻结为：

1. 输入预检查
2. `LLM rubric` 分点评价
3. 轻量一致性整理
4. 聚合输出
5. 正式结果投影

这条主线天然需要一个能表达多节点、多阶段、可追踪执行链的编排层。

`PocketFlow` 适合作为后端的 LLM 编排框架，用于组织这些阶段，但不替代应用层语义、Schema 真源或 Prompt 治理规则。

## 技术组件职责落位

### `FastAPI`

负责：

- 提供 HTTP 路由入口
- 承接请求解析与响应封装
- 对接 `apps/api/contracts/api-v0-overview.md` 中定义的资源语义
- 作为本地开发与本地部署时的后端服务入口

不负责：

- 承担完整业务编排
- 直接拼接正式 Prompt
- 直接调用 Provider SDK 并输出业务结果
- 重新定义正式结构真源

### `Pydantic`

负责：

- 表达后端边界输入输出 DTO
- 承担请求校验、响应校验与部分内部对象校验
- 作为 `FastAPI` 路由层与应用层之间的结构表达工具

不负责：

- 替代 `packages/schemas/` 成为正式结构真源
- 自行发明第二套结果语义
- 在前后端契约之外独立扩张字段定义权

说明：

- 正式结构定义的治理真源仍在 `packages/schemas/`
- `Pydantic` 是运行时表达与校验工具，不是新的契约主文档

### `DeepSeek API`

负责：

- 作为 `Phase 1` 默认且唯一正式接入的模型 Provider
- 承接正式评分主线中的模型调用
- 为 Prompt、Rubric 与聚合输出提供实际模型执行能力

不负责：

- 定义业务评分字段
- 决定任务状态机语义
- 决定前端展示逻辑

说明：

- `DeepSeek API` 是当前阶段的正式 Provider 选择
- Provider Adapter 仍然保留抽象边界，以便未来扩展其它 Provider

### `PocketFlow`

负责：

- 表达多阶段 LLM 执行链
- 组织评分主线中的节点与阶段顺序
- 为 `apps/api`、`apps/worker` 与 `evals` 提供可复用的编排抽象
- 支撑阶段执行的可追踪性与后续可视化/调试能力

不负责：

- 定义领域对象
- 定义任务状态枚举与错误语义
- 定义 Prompt 真源
- 定义正式 Schema

说明：

- `PocketFlow` 是后端编排框架，不是业务规则真源
- 评分阶段名称、阶段职责与结果语义，仍以架构文档与契约文档为准

## 部署与运行假设

### 当前部署定位

当前项目按以下方式设计：

- 作为开源项目发布
- 用户在本地安装依赖并配置环境变量
- 用户本机启动 `apps/web` 与 `apps/api`
- 如需要异步执行或回归任务，可在本机启动 `apps/worker`

### 当前不以内置假设处理的方向

当前不将以下内容作为后端路线前提：

- 公网多租户服务
- 大规模高并发流量承载
- 分布式任务系统前置依赖
- 复杂服务网格或微服务拆分
- 托管式实时推送架构

说明：

- 这不代表后续不能演进到更复杂部署模式
- 但 `Phase 1` 文档与实现都应优先满足“本地部署可用”

## 后端实现策略

### 1. API 优先承接契约

后端实现应优先围绕：

- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`

先冻结路由、状态与错误语义，再组织代码落位。

### 2. Application 优先承接用例

业务流程应先落在 `packages/application/`：

- 创建任务
- 读取任务详情
- 读取任务结果
- 执行正式评分主线
- 聚合首页摘要与历史记录

### 3. PocketFlow 优先承接评分主线

评分主线中需要多阶段 LLM 调用的部分，应优先通过 `PocketFlow` 组织，而不是把整条链路散落在路由函数中。

### 4. Pydantic 与 Schema 分层使用

建议分层方式：

- `FastAPI + Pydantic`：接口边界、请求响应 DTO、运行时校验
- `packages/schemas/`：正式结构契约真源、版本治理与跨模块统一语义

### 5. Provider 通过 Adapter 暴露

即使当前只正式接 `DeepSeek API`，也应通过 `packages/provider-adapters/` 向上暴露统一接口，而不是在 `apps/api` 或 `packages/application` 中直接写死 Provider 调用。

## 当前不采用的后端方向

当前阶段不采用：

- `Django`
- `Flask`
- 以 Web 框架直接承载完整业务编排的方式
- 以 SDK 直调脚本替代应用层编排的方式
- 以单文件临时 Prompt 调用脚本替代正式 Prompt Runtime 的方式
- 以前端直连模型 API 的方式

## 与其他文档的关系

- 系统总览见 `docs/architecture/system-overview.md`
- 应用层边界见 `docs/architecture/application-layer-boundaries.md`
- 集成边界见 `docs/architecture/integration-boundaries.md`
- Provider 抽象见 `docs/architecture/provider-abstraction.md`
- 评分流水线见 `docs/architecture/scoring-pipeline.md`
- API 契约见 `apps/api/contracts/api-v0-overview.md`
- Prompt 生命周期见 `docs/prompting/prompt-lifecycle.md`
- Schema 治理见 `docs/contracts/schema-versioning-policy.md`
