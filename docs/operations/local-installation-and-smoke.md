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

## Smoke 场景

### 1. 直接输入成功流

- 若 API 启动时无 key，先确认新建页显示 provider 未配置、创建按钮禁用、且可录入一次性 runtime key
- 在 web 新建页录入 runtime key，或确保 API 已以启动环境变量方式带 key
- 提交 `title + chapters + outline`
- 任务页从 `queued / processing` 轮询到 `completed + available`
- 任务页显示“类型识别”区域，并在分类完成后显示类型 badge、置信度和兜底标记
- 结果页展示：
  - 总体评分、总体结论、市场判断、平台候选
  - 独立类型评价模块
  - `4` 个类型 lens 卡片
  - `8` 轴 rubric 结果

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
- 若本地存有旧版结果结构，`GET /api/tasks/{taskId}/result` 会降级为 `not_available`

## 交付前最小命令检查

- `git diff --check`
- `uv run --project apps/api python -m pytest apps\api\tests\test_scoring_pipeline.py apps\api\tests\test_application.py -q`
- `uv run --project apps/api pytest apps\api\tests -q`
- `uv run --project apps/worker pytest apps\worker\tests`
- `pnpm --dir apps/web lint`
- `pnpm --dir apps/web test`
- `pnpm --dir apps/web build`

## Playwright 模式说明

### 默认 deterministic 模式

```powershell
pnpm --dir apps/web test:e2e
```

说明：

- 未显式指定 `NOVEL_EVAL_E2E_PROVIDER_MODE` 时，Playwright 默认使用 deterministic provider
- 该模式适合本地快速回归

### 真实 DeepSeek：`startup_key`

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY="<your-real-key>"
$env:NOVEL_EVAL_E2E_PROVIDER_MODE="startup_key"
pnpm --dir apps/web test:e2e
```

说明：

- API 子进程在启动时即带 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- UI 只展示“启动环境变量”状态

### 真实 DeepSeek：`runtime_key`

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY="<your-real-key>"
$env:NOVEL_EVAL_E2E_PROVIDER_MODE="runtime_key"
pnpm --dir apps/web test:e2e
```

说明：

- API 子进程以缺少启动期 key 的状态启动
- 测试流会在页面中录入一次性 runtime key

### 故障排查

- 优先查看 `apps/web/.playwright/<mode>/logs/`
- 失败时结合 Playwright trace、screenshot、video 和 API 日志定位
