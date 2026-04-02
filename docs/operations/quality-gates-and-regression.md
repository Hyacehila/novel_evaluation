# Quality Gates 与 Regression Entry

## 文档角色

本文档定义当前仓库的最小质量门禁、终止型验证入口和回归触发规则。

## 终止型原则

- 只使用能在有限时间内结束的命令
- 不把长期常驻服务当作唯一门禁
- Python 相关命令统一使用 `uv`
- web 相关命令统一使用 `pnpm --dir apps/web`

## 当前最小验证入口

### 1. Diff 检查

```text
git diff --check
```

### 2. 关键 API 回归

```powershell
uv run --project apps/api python -m pytest apps\api\tests\test_scoring_pipeline.py apps\api\tests\test_application.py -q
```

### 3. API 全量测试

```powershell
uv run --project apps/api pytest apps\api\tests -q
```

### 4. worker 基线测试

```powershell
uv run --project apps/worker pytest apps\worker\tests
```

### 5. web 基线检查

```powershell
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web build
```

### 6. Playwright E2E

快速回归：

```powershell
pnpm --dir apps/web test:e2e
```

真实 DeepSeek 验收：

```powershell
$env:NOVEL_EVAL_DEEPSEEK_API_KEY="<your-real-key>"
$env:NOVEL_EVAL_E2E_PROVIDER_MODE="startup_key"
pnpm --dir apps/web test:e2e

$env:NOVEL_EVAL_E2E_PROVIDER_MODE="runtime_key"
pnpm --dir apps/web test:e2e
```

## 何时必须触发受控回归

- `promptVersion` 变化
- `schemaVersion` 变化
- `rubricVersion` 变化
- Provider / Model 变化
- 类型目录、类型阈值或类型 lens 逻辑变化
- 上传与输入边界变化
- 状态、错误码或任务元数据语义变化
- 结果页类型模块或任务页类型识别展示变化
- `worker eval` 或 `worker batch` 的输入装配逻辑变化

## 当前不作为唯一门禁

- `uvicorn --reload`
- 长时间运行的 worker 进程
- 只有人工点击页面、没有命令校验的检查
