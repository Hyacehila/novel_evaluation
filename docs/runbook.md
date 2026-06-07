# Runbook

## 默认口径

- 默认联调与 Playwright 回归基线是 deterministic provider。
- 真实 `DeepSeek` 只作为可选验收路径，不是首次启动前提。
- API 缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时可以只读启动；此时可查看历史与结果，但不能创建新任务。
- worker 的真实 `eval` / `batch` 执行仍要求 `NOVEL_EVAL_DEEPSEEK_API_KEY`；`--dry-run` 只做路径与 runtime 预览，不要求 key。
- 创建任务必须显式选择 `analysisMode`：`long_opening_outline` 或 `completed_fulltext`。系统不再把材料不足的输入切到另一套评分提示词。

## 前置依赖

- `Python 3.13`
- `uv`
- `Node.js 20+`
- `pnpm`

## 首次启动

```powershell
.\scripts\setup.ps1
.\scripts\run-api.ps1
.\scripts\run-web.ps1
```

默认地址：

- Web: `http://127.0.0.1:3000/`
- API: `http://127.0.0.1:8000/`

如需自定义端口、数据库路径或日志目录，先复制环境模板：

```powershell
Copy-Item .env.example .env
```

## Provider 模式

默认模型为 `deepseek-v4-pro`。DeepSeek V4 的 OpenAI ChatCompletions `base_url` 仍是 `https://api.deepseek.com`，项目会显式传入 `extra_body.thinking.type` 与 `reasoning_effort`，避免依赖上游默认值。

可通过 `.env` 或当前 PowerShell 会话调整：

```powershell
$env:NOVEL_EVAL_DEEPSEEK_MODEL_ID = "deepseek-v4-pro"      # 可改 deepseek-v4-flash
$env:NOVEL_EVAL_DEEPSEEK_THINKING = "enabled"              # enabled / disabled
$env:NOVEL_EVAL_DEEPSEEK_REASONING_EFFORT = "high"         # high / max，仅 thinking=enabled 时使用
$env:NOVEL_EVAL_UPLOAD_MAX_BYTES = "10485760"              # 上传体大小上限
$env:NOVEL_EVAL_LOG_LEVEL = "INFO"                         # INFO / WARNING / ERROR 等 Python 日志级别
```

### 1. 只读模式

- 不配置 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- 可以启动 API 和 Web
- 不能创建新任务
- 适合验证安装、页面、历史读取和 SQLite 持久化

### 2. 启动期真实 key

- 在 `.env` 或当前 PowerShell 会话中设置 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- 重启 `.\scripts\run-api.ps1`
- API 状态会显示 `startup_env`
- UI 不允许替换或清空该 key

### 3. 运行时一次性 key

- API 启动时不带 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- 打开 `/tasks/new`
- 在页面录入运行时 key
- 该 key 只保存在当前 API 进程内，重启或热重载后失效

## 分析模式

`analysisMode` 是用户显式选择，不从缺正文、缺大纲等材料形状自动推断：

- `long_opening_outline`：面向长篇开篇评估，必须同时提交开篇正文和大纲。
- `completed_fulltext`：面向已完成全文评估，必须提交全文正文，不能同时提交大纲。

如果 `long_opening_outline` 缺正文或缺大纲，API 返回 `422`。如果 `completed_fulltext` 缺正文，或提交了大纲，API 同样返回 `422`。这些情况不会进入替代 Prompt，也不会产出保守版本结果。

## 常用命令

```powershell
uv run --project apps/api pytest apps/api/tests evals/tests
pnpm --dir apps/web test
pnpm --dir apps/web build
pnpm --dir apps/web test:e2e
uv run --project apps/worker worker eval --suite smoke --dry-run
```

## Playwright E2E

默认 deterministic 模式：

```powershell
pnpm --dir apps/web test:e2e
```

真实 key 的可选验收分两层，默认不会随常规 `test:e2e` 自动执行。建议先跑 auth smoke，确认 key、网络和 DeepSeek 账号状态，再按需跑完整真实 pipeline。

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY = "<redacted-local-key>"
$env:NOVEL_EVAL_DEEPSEEK_THINKING = "disabled"          # 真实 E2E 建议关闭以降低时延

$env:NOVEL_EVAL_E2E_PROVIDER_MODE = "startup_key"
$env:NOVEL_EVAL_E2E_REAL_SCOPE = "auth_smoke"
pnpm --dir apps/web test:e2e -- e2e/provider-auth-smoke.spec.ts

$env:NOVEL_EVAL_E2E_PROVIDER_MODE = "runtime_key"
pnpm --dir apps/web test:e2e -- e2e/provider-auth-smoke.spec.ts

$env:NOVEL_EVAL_E2E_PROVIDER_MODE = "startup_key"
$env:NOVEL_EVAL_E2E_REAL_SCOPE = "full_pipeline"
$env:NOVEL_EVAL_E2E_REAL_TASK_TIMEOUT_MS = "1800000"
pnpm --dir apps/web test:e2e -- e2e/provider-full-pipeline-real.spec.ts
```

模式说明：

- `deterministic`：Playwright 启动的 API 会走 deterministic 基线
- `startup_key`：E2E API 进程启动时直接带真实 key
- `runtime_key`：E2E API 进程启动时不带 key，由页面录入运行时 key
- `auth_smoke`：只调用 `/api/provider-status/smoke-test`，验证真实 provider 能返回成功响应
- `full_pipeline`：跑完整评分链；若真实模型超时或结构化输出失败，页面必须显示明确诊断

E2E 专用变量：

- `NOVEL_EVAL_E2E_PROVIDER_MODE`：`deterministic` / `startup_key` / `runtime_key`
- `NOVEL_EVAL_E2E_REAL_SCOPE`：`auth_smoke` / `full_pipeline`
- `NOVEL_EVAL_E2E_REAL_TASK_TIMEOUT_MS`：真实 full pipeline 等待任务完成的上限
- `NOVEL_EVAL_E2E_DISABLE_ARTIFACTS=1`：关闭失败 trace、截图和视频
- `NOVEL_EVAL_E2E_API_ORIGIN`：provider helper 访问 E2E API 的地址，默认 `http://127.0.0.1:18000`
- `NOVEL_EVAL_E2E_ALLOW_PROVIDER_RESET`：E2E API 启动脚本内部设置的 runtime key 重置开关，不需要手动配置
- `NOVEL_EVAL_CAPTURE_README_SCREENSHOT_PATH`：维护 README 截图时指定截图输出路径

## Smoke 与回归

- 后端基线：`uv run --project apps/api pytest apps/api/tests evals/tests`
- 前端单测：`pnpm --dir apps/web test`
- 前端构建：`pnpm --dir apps/web build`
- 浏览器流转：`pnpm --dir apps/web test:e2e`
- worker 干跑：`uv run --project apps/worker worker eval --suite smoke --dry-run`，无需配置真实 key
- worker 真实执行：先配置 `NOVEL_EVAL_DEEPSEEK_API_KEY`，再运行不带 `--dry-run` 的 `eval` / `batch`

## 故障排查

- 看到 `PROVIDER_NOT_CONFIGURED`：API 当前没有可用 key；改用启动期 key 或页面 runtime key。
- 页面无法连接 API：确认 `.\scripts\run-api.ps1` 正在运行，并检查 `.env` 中的 `NOVEL_EVAL_API_HOST` / `NOVEL_EVAL_API_PORT`。
- 运行时 key 不能录入：如果 API 已经由 `startup_env` 提供 key，UI 会锁定配置入口。
- `Provider auth smoke` 失败：优先检查 key、额度、网络和 DeepSeek 上游状态；该接口不会写入任务库。
- 真实任务失败且显示 schema 校验问题：模型返回结构化结果不满足契约，系统会重试一次并显示明确失败说明。
- 真实任务超时：缩短正文/大纲，或在 E2E 中延长 `NOVEL_EVAL_E2E_REAL_TASK_TIMEOUT_MS`。
- 历史结果读取失败：先确认本地 SQLite 是否包含不满足当前 schema 的结果；损坏结果不会伪装成成功结果。
- 想重置本地数据：关闭 API 后删除 `var/novel-evaluation.sqlite3`；下次启动会自动创建空 SQLite 库。
- 上传失败：当前只支持 `TXT`、`MD`、`DOCX`，并受 `NOVEL_EVAL_UPLOAD_MAX_BYTES` 限制。
