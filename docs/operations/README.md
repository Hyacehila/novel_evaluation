# `docs/operations`

该目录面向维护者与贡献者，冻结本地运行、配置、诊断、质量门禁和回滚规则。

第一次运行项目的用户请优先阅读：

- `docs/getting-started/quick-start.md`
- `docs/getting-started/real-provider.md`
- `docs/getting-started/faq.md`

## 主文档

- `docs/operations/local-installation-and-smoke.md`
- `docs/operations/runtime-configuration-and-diagnostics.md`
- `docs/operations/local-development-topology.md`
- `docs/operations/quality-gates-and-regression.md`
- `docs/operations/rollback-and-fallback.md`

## 当前口径

- 运维文档只服务本地单用户交付与仓库维护
- `SQLite` 是唯一正式本地状态存储
- 用户任务由 API 进程内执行，worker 只做回归与批处理
- 新环境可用性应通过安装、启动、smoke 和质量门禁共同验证
