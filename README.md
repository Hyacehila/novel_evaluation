# 小说智能打分系统仓库

本仓库当前处于**结构构建与实现准备阶段**，已完成顶层目录骨架、主线架构文档与核心治理文档落位，正在围绕已冻结的技术路线补齐可执行文档，**尚未开始大规模业务开发**。

## 当前目标

- 为小说智能打分系统建立长期可演进的仓库结构
- 冻结 `Phase 1` 的前后端实现基线与协作边界
- 将 Prompt、Schema、Provider、Evals、应用入口明确分层
- 将抓取与分析产物和正式源码彻底隔离
- 优先满足开源项目的本地部署、本机联调与本机回归

## 当前实现基线

- 前端技术路线见 `docs/architecture/frontend-technical-route.md`
- 后端技术路线见 `docs/architecture/backend-technical-route.md`
- 后端实现基线为 `Python 3.13 + uv + FastAPI + Pydantic`
- `Phase 1` 默认且唯一正式接入的模型 Provider 为 `DeepSeek API`
- 评分主线的多阶段 LLM 编排基线为 `PocketFlow`
- 项目当前部署定位为开源项目本地部署、本机启动 `apps/web` 与 `apps/api` 后使用

## 顶层目录说明

- `apps/`：可运行应用入口，包括前端、后端、异步执行层
- `packages/`：可复用核心能力，包括领域模型、应用编排、Provider 适配、Schema 等
- `prompts/`：正式 Prompt 资产，仅允许后端治理与使用
- `evals/`：评测样本、用例、基线与报告
- `docs/`：规划、架构、契约、运维、决策与研究说明
- `output/`：抓取、分析、快照与临时产物，非正式源码目录
- `scripts/`：仓库维护、评测执行、结构检查脚本

## 当前原则

- Prompt 只能在后端侧治理，不允许前端持有正式评分 Prompt
- 所有核心结构以严格 JSON 契约为基础
- 正式结构真源位于 `packages/schemas/`
- 正式评分主线采用全 `LLM` 分阶段 `rubric` 机制
- `output/playwright/` 永久视为研究/抓取产物，不纳入正式源码
- 正式实现应先遵守 `docs/` 下的规划与边界，再开始编码

## 建议阅读顺序

1. `docs/architecture/system-overview.md`
2. `docs/planning/mvp-phase-1-scope.md`
3. `docs/architecture/backend-technical-route.md`
4. `docs/decisions/ADR-005-backend-technical-route.md`
5. `docs/architecture/layered-rubric-evaluation-architecture.md`
6. `docs/contracts/rubric-stage-contracts.md`
7. `docs/architecture/scoring-pipeline.md`
8. `docs/contracts/json-contracts.md`

## 当前状态

- 已完成目录骨架创建
- 已迁移主计划文档到 `docs/planning/`
- 已建立首批架构与治理文档真源
- 已冻结正式评分主线与后端实现基线
- 正在补齐前后端协作与本地部署相关文档
- 暂未进行大规模业务开发
