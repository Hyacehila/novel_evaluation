# Quality Gates 与 Regression Entry

## 文档角色

本文档定义当前仓库的最小质量门禁、终止型验证入口和回归触发规则。

## 终止型原则

- 只使用能在有限时间内结束的命令
- 不把长期常驻服务当作唯一门禁
- Python 相关命令统一使用 `uv`

## 当前最小验证入口

### 1. Diff 检查

#### Bash / PowerShell

```text
git diff --check
```

### 2. 文档关键锚点检查

#### Bash

```bash
rg "Doc-Ready|DevFleet-Ready|Implementation-Ready|depends_on|禁止并行修改面|doc_frozen|reportType" docs apps/api/contracts evals prompts
```

#### PowerShell

```powershell
Get-ChildItem -Recurse -File docs,apps\api\contracts,evals,prompts | Select-String -Pattern 'Doc-Ready|DevFleet-Ready|Implementation-Ready|depends_on|禁止并行修改面|doc_frozen|reportType'
```

### 3. 状态与错误语义一致性检查

#### Bash

```bash
rg "queued|processing|completed|failed|available|not_available|blocked|VALIDATION_ERROR|TASK_NOT_FOUND" docs apps/api/contracts apps/api/src apps/api/tests packages/schemas
```

#### PowerShell

```powershell
Get-ChildItem -Recurse -File docs,apps\api\contracts,apps\api\src,apps\api\tests,packages\schemas | Select-String -Pattern 'queued|processing|completed|failed|available|not_available|blocked|VALIDATION_ERROR|TASK_NOT_FOUND'
```

### 4. Python 可编译性检查

#### Bash

```bash
uv run --project apps/api python -m compileall apps/api/src apps/api/tests packages
```

#### PowerShell

```powershell
uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages
```

### 5. API 基线测试

#### Bash

```bash
uv run --project apps/api pytest apps/api/tests
```

#### PowerShell

```powershell
uv run --project apps/api pytest .\apps\api\tests
```

## 何时必须触发受控回归

- `promptVersion` 变化
- `schemaVersion` 变化
- `rubricVersion` 变化
- Provider / Model 变化
- 上传与输入边界变化
- 状态或错误码语义变化

## 当前不作为唯一门禁

- `uvicorn --reload`
- 长时间运行的 worker
- 只有人工点击页面的检查
