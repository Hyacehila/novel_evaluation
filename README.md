# 小说智能打分系统仓库

本仓库当前处于**项目结构构建阶段**，已完成顶层目录骨架与核心规划文档落位，**尚未开始实际业务开发**。

## 当前目标

- 为小说智能打分系统建立长期可演进的仓库结构
- 保持技术栈中立，不预设具体前端或后端实现框架
- 将 Prompt、Schema、Provider、Evals、应用入口明确分层
- 将抓取与分析产物和正式源码彻底隔离

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
- `output/playwright/` 永久视为研究/抓取产物，不纳入正式源码
- 正式实现应先遵守 `docs/` 下的规划与边界，再开始编码

## 建议阅读顺序

1. `docs/architecture/layered-rubric-evaluation-architecture.md`
2. `docs/contracts/rubric-stage-contracts.md`
3. `docs/planning/layered-rubric-implementation-plan.md`
4. `docs/planning/rubric-design-absorption-matrix.md`
5. `docs/decisions/ADR-004-layered-rubric-evaluation.md`
6. `docs/architecture/system-overview.md`
7. `docs/contracts/json-contracts.md`

## 当前状态

- 已完成目录骨架创建
- 已迁移主计划文档到 `docs/planning/`
- 已建立首批架构与治理文档占位
- 暂未进行实际业务开发
