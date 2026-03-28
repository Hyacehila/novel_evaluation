# 前端总览

## 文档定位

本文是前端文档体系的主入口，用于统一说明前端在系统中的角色、首期范围、总体原则、主流程以及当前维护中的前端主文档。

本文承担原“总览 + 文档索引”的收口职责，并在当前阶段额外承担“前端可独立开工入口”的职责，但不替代页面规格、状态流、前后端边界或正式 Schema。

## 前端在系统中的角色

前端定位为**评测任务工作台**，负责承接用户输入、触发评测任务、展示任务状态、消费结构化结果以及支持历史回访。

前端负责：

- 接收用户输入的小说文本或文件
- 发起评测任务
- 感知任务执行状态
- 展示后端已经校验通过的结构化结果
- 支持历史任务回访

前端不负责：

- 治理正式 Prompt
- 持有 Prompt 正文或 Prompt 版本选择能力
- 适配模型供应商内部细节
- 直接消费未校验的模型原始输出
- 修复非法结果并将其当作正式结果展示

## 当前阶段与范围

当前项目已经进入真实 API 联调与持续维护阶段。前端文档当前目标是：让 `apps/web` 的页面、查询层、View Model 与本地代理实现保持一致，并为后续迭代提供稳定边界。

当前阶段已经明确：

- 页面结构与主流程
- 状态与阻断策略
- 前后端职责边界与 View Model
- 页面规格与展示边界
- 前端技术路线与模块边界
- 查询策略与最小假契约

当前阶段不做：

- 不展开具体页面与组件实现代码
- 不把历史设计稿误当作当前实现
- 不输出视觉设计稿或高保真交互稿
- 不将 `结果对比页` 推入首期核心交付
- 不把研究产物或 Mock 契约误当作正式 Schema

## 前端总体设计原则

### 1. Workflow-First

前端围绕“新建任务 -> 查看状态 -> 进入结果 -> 历史回访”的主流程组织，而不是围绕零散页面或技术模块堆叠。

### 2. 任务对象与结果对象分离

`任务详情 / 状态页` 与 `结果详情页` 必须分页分离。任务过程信息与正式结果正文不能混写。

### 3. 契约优先

前端只消费后端已经校验通过的结构化结果。正式结构定义以 `packages/schemas/` 与相关契约文档为基准。

### 4. 异常结果严格阻断

当结果不合法、不可用或读取失败时，前端不展示伪结果，只展示错误态、任务状态与必要说明。

### 5. 历史记录按任务组织

历史沉淀以 `EvaluationTask` 为主对象，而不是以结果作为首要列表对象。首页中的最近结果摘要只是快捷入口，不改变这一原则。

### 6. 摘要层与详情层分离

首页与历史记录页只承载摘要；`任务详情 / 状态页` 承载任务过程；`结果详情页` 承载正式结果全文。

### 7. 结果对比页仅结构预留

`结果对比页` 当前仅保留在信息架构中，不进入首期核心页，也不提前展开详细规格。

### 8. Adapter-First + Real-API-First

当前前端以真实 API 为默认联调路径，通过 DTO -> View Model 映射层隔离后端变化；测试可继续使用 Mock，但 Mock 已不再代表当前主运行路径。

## 首期产品范围

### 首期核心页

- `工作台首页`
- `新建评测任务页`
- `任务详情 / 状态页`
- `结果详情页`
- `历史记录页`

### 结构预留页

- `结果对比页`

## 核心任务流概览

### 主流程

1. 用户进入 `工作台首页`
2. 用户进入 `新建评测任务页`
3. 用户提交输入并创建任务
4. 用户进入 `任务详情 / 状态页`
5. 任务完成后，页面提供结果入口，由用户手动进入 `结果详情页`
6. 用户可通过 `历史记录页` 回访任务与结果

### 辅助流程

- 用户可从 `工作台首页` 的最近任务摘要进入任务详情
- 用户可从 `工作台首页` 的最近结果摘要进入结果详情
- 用户可从 `历史记录页` 进入任务详情或结果详情

### 失败路径

- 任务提交失败：停留在输入与错误提示层
- 任务执行失败：停留在 `任务详情 / 状态页`
- 结果不可用：不进入正式结果正文
- 结果被阻断：严格阻断，不展示伪结果

## 当前维护中的前端主文档

| 文档路径 | 主要职责 | 建议阅读时机 |
| --- | --- | --- |
| `docs/architecture/frontend-overview.md` | 前端总入口、总原则、文档地图 | 先读 |
| `docs/architecture/frontend-information-architecture.md` | 页面结构、对象关系、导航语义与预留页面位置 | 第二步读 |
| `docs/architecture/frontend-task-and-state-flow.md` | 任务流、状态流、失败与阻断、空态与恢复规则 | 第三步读 |
| `docs/contracts/frontend-backend-boundary.md` | 前后端职责边界、结果消费边界与提交边界 | 与状态流并行阅读 |
| `docs/contracts/frontend-view-models.md` | 前端页面消费的数据视图模型 | 进入字段设计前阅读 |
| `docs/contracts/frontend-input-and-submit-spec.md` | 输入字段、来源语义、前端边界校验与提交约束 | 设计输入页前阅读 |
| `docs/contracts/frontend-terminology.md` | 页面、对象、状态与关键字段术语统一 | 全程参考 |
| `docs/planning/frontend-page-specs.md` | 页面职责、页面模块、展示边界、历史检索与结果呈现规则 | 准备实现页面时阅读 |
| `docs/architecture/frontend-technical-route.md` | 前端框架、状态分层、表单、查询与真实 API 联调基线 | 准备固化技术方案时阅读 |
| `docs/architecture/frontend-app-shell-and-module-boundaries.md` | `apps/web` 的应用壳、目录结构、模块边界与依赖方向 | 准备搭建工程骨架时阅读 |
| `docs/contracts/frontend-api-consumption-and-query-strategy.md` | Query / Mutation、轮询、缓存、失效与映射策略 | 准备搭建数据层时阅读 |
| `docs/contracts/frontend-minimal-api-assumptions.md` | 后端未定稿阶段的最小假契约与 Mock 基线 | 准备搭建 Mock 与接口适配时阅读 |
| `docs/planning/frontend-implementation-readiness-checklist.md` | 进入 `apps/web` 实际开发前的收口检查 | 准备开发前阅读 |

## 建议阅读路径

### 路线一：首次理解前端体系

1. `docs/architecture/frontend-overview.md`
2. `docs/architecture/frontend-information-architecture.md`
3. `docs/architecture/frontend-task-and-state-flow.md`
4. `docs/contracts/frontend-backend-boundary.md`
5. `docs/planning/frontend-page-specs.md`

### 路线二：准备直接开工前端

1. `docs/architecture/frontend-overview.md`
2. `docs/architecture/frontend-information-architecture.md`
3. `docs/architecture/frontend-task-and-state-flow.md`
4. `docs/planning/frontend-page-specs.md`
5. `docs/architecture/frontend-technical-route.md`
6. `docs/architecture/frontend-app-shell-and-module-boundaries.md`
7. `docs/contracts/frontend-view-models.md`
8. `docs/contracts/frontend-input-and-submit-spec.md`
9. `docs/contracts/frontend-api-consumption-and-query-strategy.md`
10. `docs/contracts/frontend-minimal-api-assumptions.md`
11. `docs/planning/frontend-implementation-readiness-checklist.md`

### 路线三：前后端联调与契约对齐

1. `docs/contracts/frontend-backend-boundary.md`
2. `docs/contracts/frontend-minimal-api-assumptions.md`
3. `docs/contracts/frontend-api-consumption-and-query-strategy.md`
4. `docs/contracts/frontend-view-models.md`
5. `docs/contracts/frontend-input-and-submit-spec.md`
6. `docs/contracts/frontend-terminology.md`

## 当前不纳入项

当前不纳入本文与当前前端主线的内容包括：

- 具体页面与组件实现代码
- 高保真视觉设计稿与交互稿
- Prompt 调试入口
- 模型调试入口
- 研究侧独立页面
- `结果对比页` 的详细规格
- 复杂运营看板
- 多角色后台管理页
- 后端正式 API 最终定稿

## 使用建议

建议以本文作为前端文档入口，并按“总览 -> 信息架构 -> 状态流与边界 -> 页面规格 -> 技术路线 -> 模块边界 -> 查询策略与最小假契约 -> 实现检查”的顺序推进阅读与维护。
