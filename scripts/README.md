# `scripts`

## 目录角色

该目录用于承载仓库辅助脚本，是有限时、可重复执行的维护入口。

## 当前仓库现实

当前实际只有 README：

- `repo/README.md`
- `evals/README.md`
- `maintenance/README.md`

当前还没有正式脚本文件落地。

因此这里定义的是脚本分类和边界，而不是现成脚本清单。

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
- `rg "仓库维护脚本|评测执行脚本|结构检查脚本|uv run|终止条件" scripts/README.md scripts/repo/README.md scripts/evals/README.md scripts/maintenance/README.md`

## DevFleet 使用约束

- scripts 相关 mission 必须明确是 `repo`、`evals` 还是 `maintenance`
- 在脚本尚未落地前，不得把 README 文本误写成“当前已有可运行脚本集”
