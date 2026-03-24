# ADR-005：采用 FastAPI + Pydantic + DeepSeek API + PocketFlow 作为后端实现基线

## 状态

已接受。

## 背景

当前仓库已经明确以下长期约束：

- 系统核心能力是 `LLM as Judge`
- 正式评分主线固定为输入预检查、`LLM rubric` 分点评价、轻量一致性整理、聚合输出与正式结果投影
- Prompt 只允许在后端治理
- 正式输出必须是严格 JSON
- 当前仓库仍处于结构与治理优先阶段
- 项目目标是开源后由用户在本地部署并使用，而不是直接作为公网高并发网站提供服务

在这些前提下，后端如果继续保持“技术实现待定”，会导致已有的 API 契约、应用边界、Prompt 治理、Schema 治理与评分流水线难以进入真正可执行的实现准备状态。

因此需要正式冻结后端技术路线。

## 决策选项

### 方案 A：继续保持后端实现技术中立

优点：

- 文档层面保持抽象
- 暂时避免过早绑定具体框架

缺点：

- 无法把已有契约文档转化为实现准备文档
- 后端目录边界缺少真实承接方式
- 容易让后续实现阶段再次回到大范围技术争论
- 不利于本地部署型开源项目形成明确启动路径

### 方案 B：采用 `FastAPI + Pydantic + DeepSeek API + PocketFlow`

优点：

- `FastAPI` 适合承接清晰的 API 资源语义与本地开发体验
- `Pydantic` 适合承接边界 DTO 表达与运行时校验
- `DeepSeek API` 可作为当前阶段唯一正式 Provider，减少多 Provider 漂移
- `PocketFlow` 适合表达多阶段 LLM 编排链路
- 与本地部署优先、结构先行的项目定位匹配度高

缺点：

- 提前冻结实现基线后，未来调整成本会更高
- 需要明确区分 `Pydantic` 与 `packages/schemas/` 的角色
- 需要明确 `PocketFlow` 与 `packages/application/` 的边界，防止框架侵占业务语义

### 方案 C：采用更重的后端框架或分布式基础设施优先方案

优点：

- 理论上更容易向高并发或复杂部署演进
- 可以更早引入完整服务化能力

缺点：

- 与当前“本地部署优先”的定位不匹配
- 会引入超出 `Phase 1` 需要的工程复杂度
- 会弱化当前阶段“先契约、后实现”的节奏

## 决策

采用 **方案 B：`FastAPI + Pydantic + DeepSeek API + PocketFlow`** 作为当前后端实现基线。

对应约束如下：

- `FastAPI` 作为 `apps/api` 的 HTTP 接口入口框架
- `Pydantic` 作为接口边界与运行时结构表达/校验工具
- `DeepSeek API` 作为 `Phase 1` 默认且唯一正式接入的模型 Provider
- `PocketFlow` 作为 API、Worker 与 Evals 可共享的 LLM 编排框架
- 项目部署定位以本地部署、本机运行前后端为优先假设

## 具体原则

### 1. 正式结构真源不变

即使采用 `Pydantic`，正式结构契约真源仍然在 `packages/schemas/`。

### 2. 编排框架不拥有业务定义权

即使采用 `PocketFlow`，任务状态、结果状态、错误语义、阶段名称与输出字段含义，仍然由现有架构与契约文档定义。

### 3. Provider 选择已冻结，但抽象边界保留

即使 `Phase 1` 只正式接入 `DeepSeek API`，`packages/provider-adapters/` 仍然保留 Provider 抽象边界，不允许把 Provider 调用细节扩散到上层。

### 4. 部署定位优先服务本地使用

后端实现和运维文档应优先满足：

- 开发者本地运行
- 用户本地部署
- 前后端本机联调
- 本机回归执行

而不是以公网 SaaS 服务的假设为前提。

## 预期结果

若该提案被接受，系统将形成以下收益：

- 后端文档体系将从“抽象边界”进入“可执行实现准备”状态
- API、Application、Prompt Runtime、Provider Adapter、Schemas 的落位更清晰
- 前端与后端协作时，不再需要重复确认后端路线
- 后续代码实现可以围绕已冻结的技术基线直接展开

同时，也会引入以下治理要求：

- 必须持续维护 `Pydantic` 与 `packages/schemas/` 的职责边界
- 必须防止 `PocketFlow` 成为业务规则真源
- 必须保证 `DeepSeek API` 的 Provider 细节被收敛在适配层内

## 后续动作

- 新增 `docs/architecture/backend-technical-route.md`
- 更新 `README.md` 与 `docs/README.md`
- 更新系统总览、评分流水线、应用层边界、集成边界与 Provider 抽象文档
- 更新 `apps/api/README.md` 与相关目录 README
- 更新运行与本地部署拓扑文档
