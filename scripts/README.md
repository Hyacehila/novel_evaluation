# `scripts`

本目录只保留可重复执行的仓库脚本入口。

主要脚本：

- `setup.ps1`
- `run-api.ps1`
- `run-web.ps1`
- `repo/check-hygiene.ps1`
- `common.ps1`

约束：

- 脚本服务于安装、启动、回归和仓库卫生
- 脚本不是业务真源
- 新增脚本前先判断是否真的可重复执行、是否值得入库

继续阅读：

- [`../docs/runbook.md`](../docs/runbook.md)
- [`../docs/prompts-and-evals.md`](../docs/prompts-and-evals.md)
