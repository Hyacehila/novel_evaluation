# `evals`

本目录承载回归与批处理工件模型，不承接用户主流程。

保留内容：

- `datasets/`
- `cases/`
- `runners/`

运行时输出：

- `reports/`：运行报告输出目录，默认不入库
- `baselines/`：baseline 输出目录，默认不入库

触发回归的典型变更：

- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 输入边界、状态语义、错误语义

继续阅读：

- [`../docs/prompts-and-evals.md`](../docs/prompts-and-evals.md)
