# 文档入口

这个目录只保留当前现行文档，不再保留 ADR、计划稿、研究稿和历史分层目录。

## 使用者入口

1. 从 [`runbook.md`](runbook.md) 开始。
2. 遇到 provider、E2E、smoke 或故障排查问题，继续看同一份 `runbook` 的对应章节。

## 维护者入口

1. [`architecture.md`](architecture.md)：看保留模块、依赖方向和端到端数据流。
2. [`contracts.md`](contracts.md)：看代码真源、API 资源、状态语义和结果契约。
3. [`request-flow.md`](request-flow.md)：看一次 `POST /api/tasks` 后主链里每一次请求、Prompt 和评分分工。
4. [`prompts-and-evals.md`](prompts-and-evals.md)：看 Prompt 资产、选择规则、evals 和维护规则。

## 文档职责

- 根目录 `README.md` 只放项目范围、快速启动、核心验证命令和正式文档入口。
- `runbook.md` 负责运行、联调、E2E、smoke 和故障排查。
- `architecture.md` 负责模块职责、依赖方向和主链数据流。
- `contracts.md` 负责 API、Schema、状态和结果契约解释。
- `request-flow.md` 负责评分链路、stage 顺序和 Prompt 路由。
- `prompts-and-evals.md` 负责 Prompt 资产、选择规则、evals 和维护规则。
- 子项目 README 只保留该子项目职责、命令和跳转，不复制深层契约。

## 同步规则

- 代码真源优先于解释文档；发现冲突时，同一 PR 内修正文档。
- 改动 API、Schema、状态、错误码、环境变量、脚本、Prompt、evals、worker 行为或测试入口时，必须检查相关文档。
- PR 描述必须包含“文档影响”段落，取值为 `已同步`、`无需同步` 或 `待确认`。
- 仓库不再提供卫生检查脚本；维护者需要人工检查旧路径、旧术语、疑似密钥、Markdown 本地链接和代码真源一致性。

## 目录约定

- `docs/assets/` 只存放被正式文档引用的静态资源。
- 其余正式文档固定为 `README.md`、`runbook.md`、`architecture.md`、`contracts.md`、`request-flow.md`、`prompts-and-evals.md`。
