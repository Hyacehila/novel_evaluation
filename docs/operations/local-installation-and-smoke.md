# 本地 Smoke 与维护者检查

## 文档目的

本文档面向维护者与贡献者，冻结原始安装命令、维护者 smoke 场景和交付前检查。

第一次运行项目的用户请先阅读：

- `docs/getting-started/quick-start.md`
- `docs/getting-started/real-provider.md`

## 原始安装命令

- API：`uv sync --project apps/api`
- worker：`uv sync --project apps/worker`
- web：`pnpm --dir apps/web install`

## 原始启动命令

### API

```powershell
uv run --project apps/api uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

说明：

- 若需自定义端口，优先通过 `.env` 或环境变量设置 `NOVEL_EVAL_API_HOST / NOVEL_EVAL_API_PORT`
- 默认 SQLite 写入仓库根 `var/novel-evaluation.sqlite3`
- API 缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时仍可只读启动，可查看已有数据，但不能创建新分析任务
- 若需执行真实分析，需在启动前通过环境变量配置 key，或在前端录入一次性 runtime key

### web

```powershell
pnpm --dir apps/web dev -- --hostname 127.0.0.1 --port 3000
```

说明：

- web 通过同源 `/api` 代理访问后端
- 默认会把 `/api/*` 代理到 `http://127.0.0.1:8000/api/*`

### worker batch

```powershell
uv run --project apps/worker worker batch --source .\path\to\batch.json [--report-id batch_smoke] [--dry-run]
```

### worker eval

```powershell
uv run --project apps/worker worker eval --suite smoke [--baseline-id baseline_smoke] [--report-id report_smoke] [--dry-run]
```

说明：

- `worker eval` 会写出 `evals/reports/{reportId}.json` 和 `evals/reports/{reportId}.records.json`
- 传入 `--baseline-id` 时会额外写出 `evals/baselines/{baselineId}.json`
- `worker batch` 只写本地批处理摘要，不接管用户任务 SQLite

## Smoke 场景

### 1. 直接输入成功流

- 若 API 启动时无 key，先确认新建页显示 provider 未配置、创建按钮禁用、且可录入一次性 runtime key
- 在 web 新建页录入 runtime key，或确保 API 已以启动环境变量方式带 key
- 提交 `title + chapters + outline`
- 任务页从 `queued / processing` 轮询到 `completed + available`
- 结果页展示四项评分、平台建议、编辑结论和详细分析

### 2. 文件上传流

- 在 web 新建页上传 `TXT / MD / DOCX`
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
- 若使用的是 runtime key，记录其仅在当前 API 进程内有效
- 重启 API
- `GET /api/tasks/{taskId}`、`GET /api/tasks/{taskId}/result`、`GET /api/history` 仍可读取
- 若 API 重启后仍未配置启动期 key，则新建任务再次受限，需重新录入 runtime key

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

- `pnpm --dir apps/web test:e2e` 固定跑真实 `DeepSeek API`
- `startup_key` 模式要求 API 子进程在启动时即带 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- `runtime_key` 模式会让 API 子进程以缺少启动期 key 的状态启动，再由页面录入一次性 runtime key
- 若 `startup_key` 模式缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，E2E 会在启动阶段直接失败
- 若 E2E 失败，优先检查 `apps/web/.playwright/logs/api.log`
