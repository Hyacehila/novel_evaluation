# 本地安装与 Smoke

## 文档目的

本文档冻结当前仓库已落地实现的安装、启动和 smoke 命令。

## 安装命令

- API：`uv sync --project apps/api`
- worker：`uv sync --project apps/worker`
- web：`pnpm --dir apps/web install`

## 启动命令

PowerShell 真实 DeepSeek 示例：

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY = "<your-real-key>"
```

### API

`uv run --project apps/api uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000`

说明：

- 若需自定义端口，改为读取 `NOVEL_EVAL_API_HOST / NOVEL_EVAL_API_PORT`
- 默认 SQLite 将写入仓库根 `var/novel-evaluation.sqlite3`
- 若需禁止 fallback，可额外设置 `$env:NOVEL_EVAL_REQUIRE_REAL_PROVIDER = "1"`

### web

`pnpm --dir apps/web dev -- --port 3000`

说明：

- web 通过同源 `/api` 代理访问后端
- 默认会把 `/api/*` 代理到 `http://127.0.0.1:8000/api/*`

### worker batch

`uv run --project apps/worker worker batch --source .\path\to\batch.json [--report-id batch_smoke] [--dry-run]`

### worker eval

`uv run --project apps/worker worker eval --suite smoke [--baseline-id baseline_smoke] [--report-id report_smoke] [--dry-run]`

说明：

- `worker eval` 会写出 `evals/reports/{reportId}.json`、`evals/reports/{reportId}.records.json`
- 传入 `--baseline-id` 时会额外写出 `evals/baselines/{baselineId}.json`
- `worker batch` 只写本地批处理摘要，不接管用户任务 SQLite

## 启动顺序

1. 配置环境变量
2. 启动 API
3. 启动 web
4. 需要回归或批处理时再启动 worker

## Smoke 场景

### 1. 直接输入成功流

- 在 web 新建页提交 `title + chapters + outline`
- 任务页从 `queued/processing` 轮询到 `completed + available`
- 结果页展示四项评分、平台建议、编辑结论和详细分析

### 2. 文件上传流

- 在 web 新建页上传 `TXT/MD/DOCX`
- 后端成功解析 `chaptersFile` 或 `outlineFile`
- 任务页能展示 `chapters_only / outline_only / chapters_outline` 的真实语义

### 3. 阻断流

- 使用 `evals/datasets/scoring/smoke-blocked.json` 或构造跨输入冲突样本
- 任务进入 `completed + blocked`
- 结果页不展示伪结果，只展示阻断态

### 4. 失败流

- 通过 provider/schema 注入失败样本或人为破坏 provider 返回
- 任务进入 `failed + not_available`
- 任务页可读取 `errorCode` 与 `errorMessage`

### 5. 重启后历史可读流

- 完成至少一个任务并确认写入 SQLite
- 重启 API
- `GET /api/tasks/{taskId}`、`GET /api/tasks/{taskId}/result`、`GET /api/history` 仍可读取

## 交付前最小命令检查

- `git diff --check`
- `uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages .\evals`
- `uv run --project apps/api pytest .\apps\api\tests .\evals\tests`
- `uv run --project apps/worker pytest .\apps\worker\tests`
- `pnpm --dir apps/web lint`
- `pnpm --dir apps/web test`
- `pnpm --dir apps/web build`
- 在已设置 `NOVEL_EVAL_DEEPSEEK_API_KEY` 的会话中执行 `pnpm --dir apps/web test:e2e`

## Playwright 全量真实 E2E

- `pnpm --dir apps/web test:e2e` 现在固定跑真实 `DeepSeek API`
- 脚本会自动给 API 子进程注入 `NOVEL_EVAL_REQUIRE_REAL_PROVIDER=1`
- 若缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，E2E 会在启动阶段直接失败，而不是回退到 deterministic adapter
- 若 E2E 失败，优先检查 `apps/web/.playwright/logs/api.log`
