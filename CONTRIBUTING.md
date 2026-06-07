# 贡献指南

感谢你关注这个项目。当前仓库优先服务一个清晰范围内的开源版本：本地部署、单用户、`SQLite` 持久化、`api` 进程内执行用户任务、`worker` 只负责 `eval / batch`。

## 提交前建议

- 大改动先开 issue 或 discussion，先对齐目标和范围
- 小修复可以直接发 PR
- PR 描述必须包含“文档影响”段落，取值为 `已同步`、`无需同步` 或 `待确认`
- 若代码真源与解释文档冲突，以代码真源为准，并在同一 PR 修正文档

## 本地开发

推荐先用 PowerShell 包装脚本完成环境准备和日常启动：

```powershell
.\scripts\setup.ps1
.\scripts\run-api.ps1
.\scripts\run-web.ps1
```

如果你要跑维护者命令、回归或批处理，请阅读：

- `docs/runbook.md`
- `docs/prompts-and-evals.md`

## 提交 PR 前的最小检查

```powershell
git diff --check
uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages .\evals
uv run --project apps/api pytest .\apps\api\tests .\evals\tests
uv run --project apps/worker pytest .\apps\worker\tests
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web build
```

如果你改动了真实模型链路或 E2E，请在配置 `NOVEL_EVAL_DEEPSEEK_API_KEY` 后补跑：

```powershell
pnpm --dir apps/web test:e2e
```

## 文档同步规则

本仓库采用维护者优先的人工清单机制，不再提供仓库卫生检查脚本。维护者需要人工比对 API、Schema、环境变量、命令、Prompt 列表和 Markdown 本地链接。

以下改动必须检查是否同步 README、`docs/`、子项目 README、脚本说明或测试命令：

- API 路由、状态语义、错误码、请求结构和响应结构
- `packages/schemas/`、`apps/web/src/api/contracts.ts`、前端页面路由或展示字段
- `.env.example`、启动脚本、运行命令、端口、数据库路径和 provider 配置
- Prompt registry、version、scoring 文件、evals 数据集和 worker `eval` / `batch` 行为
- 测试入口、推荐验证命令、真实 DeepSeek E2E 流程和验收口径

文档职责边界：

- `README.md`：项目范围、快速启动、核心验证命令和正式文档入口
- `docs/runbook.md`：运行、联调、E2E、smoke 和故障排查
- `docs/architecture.md`：模块职责、依赖方向和主链数据流
- `docs/contracts.md`：API、Schema、状态和结果契约解释
- `docs/request-flow.md`：评分链路、stage 顺序和 Prompt 路由
- `docs/prompts-and-evals.md`：Prompt 资产、选择规则、evals 和维护规则
- 子项目 README：只保留该子项目职责、命令和跳转，不复制深层契约

维护者重点复核：

- 改动 `docs/contracts.md`、`docs/request-flow.md`、`prompts/` 或 `packages/schemas/` 时，必须人工核对对应代码真源
- 文档中的命令必须能对应当前脚本、`pyproject.toml` 或 `package.json`
- API 路由、任务状态、`analysisMode`、环境变量和 Prompt ID 必须与代码真源及 `.env.example` 一致
- README 不重复维护深层架构细节，维护者文档不面向首次用户堆砌操作步骤

## 变更原则

- 不要把用户任务从 `api` 进程内执行偷偷迁移到 `worker`
- 不要在 README 里重复维护深度架构细节
- 不要在前端、API 或脚本里发明第二套状态和错误码语义

## 许可证

提交到本仓库的代码、文档和脚本默认按仓库根目录的 [Apache License 2.0](LICENSE) 许可发布。
