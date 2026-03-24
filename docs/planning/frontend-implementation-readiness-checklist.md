# 前端实现准备清单

## 文档目的

本文用于在进入 `apps/web` 实际开发前，检查前端文档、边界、页面、状态、展示规则与实现层路线是否已经足够稳定，并确认前端是否已达到“可基于 Mock / 适配层独立开工”的状态。

## 使用方式

在开始实际开发前，逐项确认以下清单。若关键项未完成，应优先补文档，而不是直接进入实现。

## 清单

### 一、总览与基线

- [ ] `docs/architecture/frontend-overview.md` 已完成
- [ ] 前端定位为评测任务工作台已明确
- [ ] 首期核心页与结构预留页已明确
- [ ] 文档主入口与建议阅读顺序已明确

### 二、页面与信息架构

- [ ] `docs/architecture/frontend-information-architecture.md` 已完成
- [ ] 页面结构基线已稳定
- [ ] 概念路由语义与导航模型已稳定
- [ ] `结果对比页` 仅作为结构预留已明确

### 三、边界与契约

- [ ] `docs/contracts/frontend-backend-boundary.md` 已完成
- [ ] `docs/contracts/frontend-view-models.md` 已完成
- [ ] `docs/contracts/frontend-input-and-submit-spec.md` 已完成
- [ ] 首期基础元信息展示范围已明确
- [ ] 前端不持有 Prompt 的边界已明确

### 四、流程与状态

- [ ] `docs/architecture/frontend-task-and-state-flow.md` 已完成
- [ ] 输入、任务、结果三层状态命名已统一
- [ ] 失败与阻断策略已统一
- [ ] 手动进入结果页策略已明确
- [ ] 页面空态、错误态与恢复入口规则已稳定

### 五、页面规格与展示规则

- [ ] `docs/planning/frontend-page-specs.md` 已完成
- [ ] 首页结果摘要仅作快捷入口的规则已明确
- [ ] 历史记录页按任务组织的规则已明确
- [ ] 任务页与结果页的展示边界已明确
- [ ] 结果页可视化仅作辅助层的规则已明确
- [ ] 历史记录页首期检索范围已明确

### 六、实现层路线

- [ ] `docs/architecture/frontend-technical-route.md` 已完成
- [ ] `docs/architecture/frontend-app-shell-and-module-boundaries.md` 已完成
- [ ] 前端框架、UI 基线、表单与查询基线已明确
- [ ] `apps/web` 的模块分层、目录结构与依赖方向已明确
- [ ] Mock-First + Adapter-First 的开工策略已明确

### 七、API 消费与最小假契约

- [ ] `docs/contracts/frontend-api-consumption-and-query-strategy.md` 已完成
- [ ] `docs/contracts/frontend-minimal-api-assumptions.md` 已完成
- [ ] Query / Mutation 边界已明确
- [ ] 任务状态轮询策略已明确
- [ ] 前端可在后端未定稿前基于最小假契约推进

### 八、术语统一

- [ ] `docs/contracts/frontend-terminology.md` 已完成
- [ ] 页面命名已统一
- [ ] 对象命名已统一
- [ ] 状态命名已统一
- [ ] 展示术语已统一

## 进入实现的建议门槛

满足以下条件后，才建议进入前端实际开发：

- 核心页面文档与信息架构已稳定
- 状态流与异常阻断策略已稳定
- 输入与结果消费边界已稳定
- 技术路线、模块边界与查询策略已稳定
- 最小假契约已足以支撑 Mock 与页面开发
- 术语、导航与展示层级已稳定
- 不再需要依赖已废弃的拆分文档来解释主流程
- 在后端尚未完整设计时，前端仍可基于 Mock / 适配层独立开工

## 与其他文档的关系

本文是收口清单，不替代任何架构、契约或页面规格文档。
