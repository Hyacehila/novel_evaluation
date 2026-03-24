# 仓库重构执行清单

本清单用于承接当前阶段的结构构建工作，不涉及实际业务开发。

## 已完成

- 建立可承载后续技术路线冻结的顶层目录骨架
- 将主计划文档迁移到 `docs/planning/`
- 明确 `output/playwright/` 为研究/抓取产物
- 创建首批入口说明文档

## 当前阶段待完成

### 1. 结构文档

- [x] `README.md`
- [x] `docs/architecture/repository-layout.md`
- [x] `docs/architecture/system-overview.md`
- [x] `docs/architecture/domain-model.md`
- [x] `docs/architecture/scoring-pipeline.md`
- [x] `docs/architecture/provider-abstraction.md`
- [x] `docs/architecture/evals-framework.md`
- [x] `docs/contracts/json-contracts.md`

### 2. 决策记录

- [x] `docs/decisions/ADR-001-repo-structure.md`
- [x] `docs/decisions/ADR-002-prompt-governance.md`
- [x] `docs/decisions/ADR-003-output-artifacts-boundary.md`

### 3. 产品与研究文档

- [x] `docs/product/glossary.md`
- [x] `docs/research/playwright-assets-inventory.md`

### 4. 后续阶段准备

- [ ] 形成 MVP 结构任务拆解
- [ ] 形成应用层边界说明
- [ ] 形成 Schema 版本治理说明
- [ ] 形成 Prompt 生命周期说明

## 后续建议顺序

1. 先完成全部结构与治理文档
2. 再确认 MVP 范围与第一批实现对象
3. 最后再进入实际开发
