# 文档入口

这个目录只保留当前现行文档，不再保留 ADR、计划稿、研究稿和历史分层目录。

## 使用者入口

1. 从 [`runbook.md`](runbook.md) 开始。
2. 遇到 provider、E2E、smoke 或故障排查问题，继续看同一份 `runbook` 的对应章节。

## 维护者入口

1. [`architecture.md`](architecture.md)：看保留模块、依赖方向和端到端数据流。
2. [`contracts.md`](contracts.md)：看代码真源、API 资源、状态语义和结果契约。
3. [`prompts-and-evals.md`](prompts-and-evals.md)：看 Prompt 资产、选择规则、evals 和仓库卫生检查。

## 目录约定

- `docs/assets/` 只存放被正式文档引用的静态资源。
- 其余正式文档固定为 `README.md`、`runbook.md`、`architecture.md`、`contracts.md`、`prompts-and-evals.md`。
