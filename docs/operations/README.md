# `docs/operations`

该目录用于冻结 `Phase 1` 的本地运行、安装、配置、诊断、质量门禁和回滚规则。

## 主文档

- `docs/operations/runtime-configuration-and-diagnostics.md`
- `docs/operations/local-installation-and-smoke.md`
- `docs/operations/local-development-topology.md`
- `docs/operations/quality-gates-and-regression.md`
- `docs/operations/rollback-and-fallback.md`

## 当前口径

- 运维文档只服务 `Phase 1` 本地单用户交付
- `SQLite` 是唯一正式本地状态存储
- 用户任务由 API 进程内执行，worker 只做回归与批处理
- 新环境可用性必须以安装、启动和 smoke 文档验证
