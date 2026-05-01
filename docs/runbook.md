# Runbook

## 默认口径

- 默认联调与 Playwright 回归基线是 deterministic provider。
- 真实 `DeepSeek` 只作为可选验收路径，不是首次启动前提。
- API 缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时可以只读启动；此时可查看历史与结果，但不能创建新任务。
- worker 的真实 `eval` / `batch` 执行仍要求 `NOVEL_EVAL_DEEPSEEK_API_KEY`；`--dry-run` 只做路径与 runtime 预览，不要求 key。

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

## 常用命令

```powershell
uv run --project apps/api pytest apps/api/tests evals/tests
pnpm --dir apps/web test
pnpm --dir apps/web build
pnpm --dir apps/web test:e2e
uv run --project apps/worker worker eval --suite smoke --dry-run
.\scripts\repo\check-hygiene.ps1
```

## Playwright E2E

默认 deterministic 模式：

```powershell
pnpm --dir apps/web test:e2e
```

真实 key 的可选验收：

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY = "<your-key>"
$env:NOVEL_EVAL_E2E_PROVIDER_MODE = "startup_key"
pnpm --dir apps/web test:e2e
$env:NOVEL_EVAL_E2E_PROVIDER_MODE = "runtime_key"
pnpm --dir apps/web test:e2e
```

模式说明：

- `deterministic`：Playwright 启动的 API 会走 deterministic 基线
- `startup_key`：E2E API 进程启动时直接带真实 key
- `runtime_key`：E2E API 进程启动时不带 key，由页面录入运行时 key

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
- 历史结果显示 `not_available`：旧结构或损坏的结果会在读取期降级，不会伪装成成功结果。
- 想重置本地数据：关闭 API 后删除 `var/novel-evaluation.sqlite3`。
- 上传失败：当前只支持 `TXT`、`MD`、`DOCX`，并受 `NOVEL_EVAL_UPLOAD_MAX_BYTES` 限制。
