# `docs`

该目录承载项目的正式真源文档。临时差距报告不再保留为长期入口；范围、架构、契约、运维和实施计划都应各归其位。

## 子目录

- `planning/`：范围冻结、实施路线、mission 规划、覆盖矩阵
- `architecture/`：系统结构、运行模型、分层边界
- `contracts/`：API、Schema、Provider、上传与前端协作契约
- `operations/`：本地运行、安装、配置、诊断、回滚、质量门禁
- `decisions/`：ADR 与关键决策记录
- `product/`：术语和业务词表
- `research/`：研究材料，不拥有正式定义权

## 使用原则

- 单一规则只在一个主文档冻结，其它文档引用而不重复定义
- README、空目录和占位说明不计入已实现能力
- 当前唯一交付口径是 `Phase 1` 的本地单用户版本
- 若规则已经冻结到真源文档，不得在实现阶段暗中改口

## 关键真源

### 范围与计划

- `docs/planning/mvp-phase-1-scope.md`
- `docs/planning/layered-rubric-implementation-plan.md`
- `docs/planning/devfleet-mission-catalog.md`
- `docs/planning/devfleet-mission-dag.md`

### 运行模型与架构

- `docs/architecture/system-overview.md`
- `docs/architecture/runtime-execution-and-persistence.md`
- `docs/architecture/backend-technical-route.md`
- `docs/architecture/application-layer-boundaries.md`
- `docs/architecture/integration-boundaries.md`

### 契约

- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/file-upload-and-ingestion-boundary.md`
- `docs/contracts/provider-execution-contract.md`
- `docs/contracts/rubric-stage-contracts.md`
- `docs/contracts/canonical-schema-index.md`

### 运维与交付

- `docs/operations/runtime-configuration-and-diagnostics.md`
- `docs/operations/local-installation-and-smoke.md`
- `docs/operations/local-development-topology.md`
- `docs/operations/quality-gates-and-regression.md`
- `docs/operations/rollback-and-fallback.md`
