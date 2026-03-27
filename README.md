# 小说智能打分系统仓库

本仓库当前锚定的唯一交付目标仍是 `Phase 1`：开源、本地部署、单用户、可运行的小说智能打分系统。正式交付边界继续冻结为 `SQLite` 单文件持久化、`apps/api` 进程内异步执行用户任务、`worker` 只承接回归与批处理、上传格式固定为 `TXT/MD/DOCX`、前端固定为 `Next.js App Router + TypeScript + pnpm`。

## Phase 1 冻结结论

- 后端基线：`Python 3.13 + uv + FastAPI + Pydantic`
- 前端基线：`Next.js (App Router) + React + TypeScript + pnpm`
- Provider：`DeepSeek API`，未配置 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时回退本地 deterministic adapter
- 严格真实 Provider 模式：设置 `NOVEL_EVAL_REQUIRE_REAL_PROVIDER=1` 后，若缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，API 启动直接失败
- 评分编排：`PocketFlow` 只进入应用层编排模块
- 本地状态存储：`SQLite`
- 默认数据库路径：`./var/novel-evaluation.sqlite3`
- 默认日志目录：`./var/logs`
- 默认 Prompt 根目录：`./prompts`
- 用户任务执行模型：`apps/api` 进程内异步执行
- `worker` 职责：只运行批处理与回归
- 历史查询：正式支持 `q/status/cursor/limit`
- 当前继续排除：鉴权、多租户、`SSE`、`WebSocket`、多 Provider 生产级切换

## 当前现实

- `uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages .\evals` 已通过
- `uv run --project apps/api pytest .\apps\api\tests .\evals\tests` 已通过
- `uv run --project apps/worker pytest .\apps\worker\tests` 已通过
- `pnpm --dir apps/web lint`、`pnpm --dir apps/web test`、`pnpm --dir apps/web build` 已通过
- 正式五段主线、Prompt runtime、provider fallback、SQLite 持久化、history 查询、worker eval/batch、web 五页闭环都已接上

当前建议判断：

- `Doc-Ready = Yes`
- `Implementation-Ready = Yes`
- `Runtime-Ready = Yes`
- `End-to-End Alpha = Yes`
- `Delivery-Ready = Partial`

说明：

- 仓库内命令、配置和页面闭环已经对齐
- 新机器从零安装到 smoke 的演练步骤已文档化
- 是否把阶段正式上调为 `Delivery-Ready = Yes`，仍建议在一台全新环境按 `docs/operations/local-installation-and-smoke.md` 完整走一次后再落锤

## 顶层目录

- `apps/`：可运行应用入口，包含 `api`、`web`、`worker`
- `packages/`：可复用核心模块，包含 application、provider-adapters、prompt-runtime、schemas 等
- `prompts/`：正式 Prompt 资产与版本元数据
- `evals/`：评测样本、用例、runner、baseline、report
- `docs/`：范围、架构、契约、运维、决策与实施计划
- `output/`：批处理输出和临时产物
- `scripts/`：仓库维护和自动化脚本

## 常用命令

- API 安装：`uv sync --project apps/api`
- worker 安装：`uv sync --project apps/worker`
- web 安装：`pnpm --dir apps/web install`
- API 启动：`uv run --project apps/api uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000`
- web 启动：`pnpm --dir apps/web dev -- --port 3000`
- Playwright E2E：在已设置 `NOVEL_EVAL_DEEPSEEK_API_KEY` 的 PowerShell 会话中执行 `pnpm --dir apps/web test:e2e`
- worker eval：`uv run --project apps/worker worker eval --suite smoke`
- worker batch：`uv run --project apps/worker worker batch --source .\evals\datasets\scoring\smoke-available.json`

PowerShell 示例：

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY = "<your-real-key>"
pnpm --dir apps/web test:e2e
```

## 关键文档

1. `docs/operations/local-installation-and-smoke.md`
2. `docs/operations/runtime-configuration-and-diagnostics.md`
3. `docs/operations/quality-gates-and-regression.md`
4. `docs/operations/rollback-and-fallback.md`
5. `docs/contracts/canonical-schema-index.md`
6. `docs/architecture/runtime-execution-and-persistence.md`
7. `docs/architecture/scoring-pipeline.md`
8. `docs/planning/layered-rubric-implementation-plan.md`
