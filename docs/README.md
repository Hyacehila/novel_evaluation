# `docs`

该目录承载项目的正式文档真源，并按不同读者分层组织入口。

## 先看哪里

面向第一次运行项目的用户：

- `docs/getting-started/quick-start.md`
- `docs/getting-started/real-provider.md`
- `docs/getting-started/faq.md`

面向维护者和贡献者：

- `docs/operations/local-installation-and-smoke.md`
- `docs/operations/runtime-configuration-and-diagnostics.md`
- `docs/operations/quality-gates-and-regression.md`
- `docs/operations/rollback-and-fallback.md`

面向需要理解边界和真源的开发者：

- `docs/architecture/system-overview.md`
- `docs/contracts/canonical-schema-index.md`
- `docs/decisions/`
- `docs/planning/`

## 子目录

- `getting-started/`：用户入口，包含快速开始、真实 Provider 配置和 FAQ
- `planning/`：范围冻结、实施路线、mission 规划、覆盖矩阵
- `architecture/`：系统结构、运行模型、分层边界
- `contracts/`：API、Schema、Provider、上传与前端协作契约
- `operations/`：维护者文档，包含 smoke、配置、诊断、回滚和质量门禁
- `decisions/`：ADR 与关键决策记录
- `product/`：术语和业务词表
- `research/`：研究材料，不拥有正式定义权

## 使用原则

- 单一规则只在一个主文档冻结，其它文档引用而不重复定义
- README 与索引文档负责导航，不单独代表功能已实现
- 当前唯一正式交付口径是本地单用户版本
- 若规则已经冻结到真源文档，不得在实现阶段暗中改口
