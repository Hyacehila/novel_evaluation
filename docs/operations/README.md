# `docs/operations`

该目录用于记录系统运行、交付、质量门禁与失败退出相关的运维文档。

## 当前主文档

- `docs/operations/local-development-topology.md`：本机启动 `apps/web`、`apps/api`、`apps/worker` 的运行假设与组件关系
- `docs/operations/quality-gates-and-regression.md`：最小质量门禁、终止型验证入口与回归触发规则
- `docs/operations/rollback-and-fallback.md`：Prompt / Schema / Provider / Worker / Evals 的回滚与降级语义

## 当前状态

- 当前已冻结“开源项目、本地部署、本机联调”的运行前提
- 运维文档优先服务本地开发者与本地部署用户
- 当前不以内置公网高并发或复杂分布式运维方案为前提

## DevFleet 作用

该目录当前主要为 DevFleet 提供：

- 终止型验证入口
- 回归触发规则
- 失败退出与回滚主文档
- 不适合并行/不适合长时运行的约束说明
