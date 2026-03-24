# `docs`

该目录用于承载项目的正式文档体系。

## 当前子目录

- `planning/`：规划文档与任务清单
- `architecture/`：结构设计与系统边界
- `product/`：术语、业务对象与产品说明
- `decisions/`：ADR 与关键决策记录
- `contracts/`：结构契约说明
- `operations/`：运行、交付与质量门禁说明
- `research/`：研究资料与研究结论整理

## 原则

- 文档优先解释边界、职责和原因
- 不将临时抓取产物直接放入 `docs/`
- 正式评分主线应在真源文档中单点定义，再由其它文档引用
- 技术路线一旦冻结，应通过架构文档与 ADR 同步回写全仓库

## 当前关键真源

### 系统与范围

- `docs/architecture/system-overview.md`
- `docs/planning/mvp-phase-1-scope.md`

### 评分主线与契约

- `docs/architecture/layered-rubric-evaluation-architecture.md`
- `docs/contracts/rubric-stage-contracts.md`
- `docs/architecture/scoring-pipeline.md`
- `docs/contracts/json-contracts.md`

### 技术路线与决策

- `docs/architecture/frontend-technical-route.md`
- `docs/architecture/backend-technical-route.md`
- `docs/decisions/ADR-004-layered-rubric-evaluation.md`
- `docs/decisions/ADR-005-backend-technical-route.md`
