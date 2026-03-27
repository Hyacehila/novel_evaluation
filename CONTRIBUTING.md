# 贡献指南

感谢你关注这个项目。当前仓库优先服务一个清晰范围内的开源版本：本地部署、单用户、`SQLite` 持久化、`api` 进程内执行用户任务、`worker` 只负责 `eval / batch`。

## 提交前建议

- 大改动先开 issue 或 discussion，先对齐目标和范围
- 小修复可以直接发 PR
- 若改动涉及命令、环境变量、启动流程或公开行为，请同步更新 README 或对应文档

## 本地开发

推荐先用 PowerShell 包装脚本完成环境准备和日常启动：

```powershell
.\scripts\setup.ps1
.\scripts\run-api.ps1
.\scripts\run-web.ps1
```

如果你要跑维护者命令、回归或批处理，请阅读：

- `docs/operations/local-installation-and-smoke.md`
- `docs/operations/quality-gates-and-regression.md`

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

以下改动通常需要同步更新文档：

- README 中展示的启动方式和入口
- `.env.example` 或运行时环境变量
- `worker`、`api`、`web` 的职责边界
- 公开 API、Schema 或任务状态语义

文档入口建议：

- 用户入口：`docs/getting-started/`
- 维护者入口：`docs/operations/`
- 深度真源：`docs/architecture/`、`docs/contracts/`、`docs/decisions/`

## 变更原则

- 不要把用户任务从 `api` 进程内执行偷偷迁移到 `worker`
- 不要在 README 里重复维护深度架构细节
- 不要在前端、API 或脚本里发明第二套状态和错误码语义

## 许可证

提交到本仓库的代码、文档和脚本默认按仓库根目录的 [Apache License 2.0](LICENSE) 许可发布。
