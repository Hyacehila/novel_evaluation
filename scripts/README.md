# `scripts`

## 目录角色

该目录用于承载仓库辅助脚本，是有限时、可重复执行的维护入口。

## 官方入口脚本

- `setup.ps1`：安装 `api`、`worker` 和 `web` 依赖，并在缺少 `.env` 时自动复制模板
- `run-api.ps1`：读取仓库根 `.env` 后启动本地 API 开发服务
- `run-web.ps1`：读取仓库根 `.env` 后启动本地 web 开发服务
- `common.ps1`：供上述脚本复用的内部辅助函数

## 子目录

- `repo/`：仓库结构和一致性检查脚本
- `evals/`：评测执行、baseline 与 report 辅助脚本
- `maintenance/`：日常维护和清理脚本

## 允许放置的内容

- 仓库维护脚本
- 评测执行脚本
- 结构检查脚本
- 非业务核心的自动化工具

## 不建议放置的内容

- 正式评分逻辑
- Provider 适配逻辑
- 页面业务逻辑
- 无法复用的临时实验代码
- 只有人工交互、没有终止条件的脚本

## 原则

- 脚本应优先服务终止型检查、回归执行和仓库维护
- 脚本不能反向成为业务真源
- Python 脚本统一使用 `uv run`

## 验收方式

当前最小验收方式：

- `git diff --check`
- `Get-Command .\scripts\setup.ps1,.\scripts\run-api.ps1,.\scripts\run-web.ps1`

## DevFleet 使用约束

- scripts 相关 mission 必须明确是 `repo`、`evals` 还是 `maintenance`
- 对用户可见的启动脚本应优先放在 `scripts/` 根目录，避免埋在深层子目录
