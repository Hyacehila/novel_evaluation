# Quality Gates 与 Regression Entry

## 文档角色

本文档定义当前仓库在 `DevFleet-Ready` 阶段的最小质量门禁、终止型验证入口和回归触发规则。

它回答以下问题：

- 当前改文档、契约或 Python 代码时，至少要跑哪些检查
- 哪些命令是当前仓库真实可执行的终止型入口
- 哪些命令只是开发辅助，不应当作唯一验收方式
- Windows / PowerShell 下如何执行同一组最小验证

## 当前前提

- 当前仓库仍以文档收口、契约冻结和最小后端基线为主
- `apps/api/pyproject.toml`、`apps/api/src/` 与 `apps/api/tests/` 已经落地
- 当前可以运行有限、可终止的 Python 编译与 `pytest` 检查
- 当前没有 CI 流水线、没有 E2E、也不要求长期常驻服务作为唯一验收入口

## 终止型原则

- 只使用能在有限时间内结束的命令
- 不把 `uvicorn --reload`、手工点击页面、长时间观察日志当作唯一门禁
- 命令必须能从仓库根目录直接定位到真实项目入口
- Python 相关命令统一使用 `uv`

## 当前最小验证入口

### 1. Diff 与空白字符检查

#### Bash

```bash
git diff --check
```

#### PowerShell

```powershell
git diff --check
```

用途：

- 检查尾随空格
- 检查冲突标记
- 检查基础 diff 质量

### 2. 文档与契约关键字检查

#### Bash

```bash
rg "Doc-Ready|DevFleet-Ready|Implementation-Ready|depends_on|禁止并行修改面|schema_pending|doc_frozen" docs apps/api/contracts evals prompts
```

#### PowerShell

```powershell
rg 'Doc-Ready|DevFleet-Ready|Implementation-Ready|depends_on|禁止并行修改面|schema_pending|doc_frozen' docs apps/api/contracts evals prompts
```

用途：

- 检查 readiness、mission、schema 索引与治理文档锚点是否仍在

### 3. 状态与错误语义一致性检查

#### Bash

```bash
rg "queued|processing|completed|failed|available|not_available|blocked|VALIDATION_ERROR|TASK_NOT_FOUND" docs apps/api/contracts apps/api/src apps/api/tests packages/schemas
```

#### PowerShell

```powershell
rg 'queued|processing|completed|failed|available|not_available|blocked|VALIDATION_ERROR|TASK_NOT_FOUND' docs apps/api/contracts apps/api/src apps/api/tests packages/schemas
```

用途：

- 检查任务状态、结果状态与关键错误码是否在文档和代码间一致

### 4. Python 可编译性检查

#### Bash

```bash
uv run --project apps/api python -m compileall apps/api/src apps/api/tests packages
```

#### PowerShell

```powershell
uv run --project apps/api python -m compileall .\apps\api\src .\apps\api\tests .\packages
```

用途：

- 检查当前 Python 源码是否至少可以通过语法级编译
- 覆盖 API、测试以及共享 `packages/` 下已落地 Python 文件

### 5. API 基线测试

#### Bash

```bash
uv run --project apps/api pytest apps/api/tests
```

#### PowerShell

```powershell
uv run --project apps/api pytest .\apps\api\tests
```

用途：

- 验证当前最小 FastAPI 路由、应用服务和 schema 约束
- 这是当前仓库已经真实存在的最小自动化回归入口

### 6. Prompt / Evals / 模块 README 合同检查

#### Bash

```bash
rg "promptVersion|schemaVersion|rubricVersion|providerId|modelId|inputComposition|EvaluationTask|EvaluationResultResource|验收方式|回滚" docs evals prompts packages apps/worker scripts
```

#### PowerShell

```powershell
rg 'promptVersion|schemaVersion|rubricVersion|providerId|modelId|inputComposition|EvaluationTask|EvaluationResultResource|验收方式|回滚' docs evals prompts packages apps/worker scripts
```

用途：

- 检查治理文档和模块 README 是否已经从目录说明升级为可开发合同入口

## 变更类型到检查的映射

| 变更类型 | 最低必须检查 |
| --- | --- |
| `docs/planning/*` readiness / mission 文档 | `git diff --check` + 文档与契约关键字检查 |
| `docs/contracts/*` 契约文档 | `git diff --check` + 状态与错误语义一致性检查 |
| `apps/api/contracts/*` API 契约文档 | `git diff --check` + 状态与错误语义一致性检查 |
| `docs/operations/*` 运维文档 | `git diff --check` + Prompt / Evals / 模块 README 合同检查 |
| `prompts/*` 治理文档 | `git diff --check` + Prompt / Evals / 模块 README 合同检查 |
| `evals/*` 治理文档 | `git diff --check` + Prompt / Evals / 模块 README 合同检查 |
| `packages/*/README.md` / `apps/worker/README.md` / `scripts/*` | `git diff --check` + Prompt / Evals / 模块 README 合同检查 |
| `apps/api/**/*.py` 或 `packages/**/*.py` | `git diff --check` + Python 可编译性检查 + API 基线测试 |

## 何时必须触发受控回归

以下变化至少应触发一次受控回归审查：

- 正式 Prompt 版本变化
- `schemaVersion` 变化
- `rubricVersion` 变化
- 阶段契约字段或枚举变化
- 任务状态或结果状态语义变化
- 错误码集合变化
- `fatalRisk` 词表变化
- `providerId` / `modelId` 变化

说明：

- 当前受控回归可以先落在 `apps/api/tests/`、`evals/` 治理文档和报告记录层
- 当前不要求先有完整 runner 才允许记录回归结论

## DevFleet 环境下明确不作为唯一门禁的方式

以下方式可以辅助开发，但不应作为唯一验收入口：

- `uv run --project apps/api uvicorn api.app:create_app --reload`
- 长时间运行的 worker
- 只能靠浏览器手工点击、没有终止条件的检查
- 需要人工长时间盯日志的命令

## 报告产物位置

当前约定：

- Python 自动化基线在 `apps/api/tests/`
- 结构化回归报告未来落在 `evals/reports/`
- 基线记录未来落在 `evals/baselines/`
- 文档收口阶段的验收结论主要落在 `docs/operations/` 与 `docs/planning/`

## 当前最小通过标准

在当前 `DevFleet-Ready` 阶段，最小通过标准是：

- `git diff --check` 通过
- 文档与代码中的状态、错误、版本锚点没有明显冲突
- `uv run --project apps/api python -m compileall ...` 通过
- `uv run --project apps/api pytest apps/api/tests` 通过
- 模块 README、Prompt、Evals 与运维文档不再只是目录说明

## 当前不包含的内容

本文档当前不要求：

- 覆盖率门槛
- 集成测试流水线
- E2E 自动化
- 部署后健康检查
- 长驻式性能压测

这些内容属于 `Implementation-Ready` 之后再逐步补齐的能力。

## 完成标准

满足以下条件时，可认为当前仓库已有最小可执行质量门禁：

- 每类主要变更都能指向至少一条真实存在的终止型检查
- Windows / PowerShell 与 Bash 都有可直接执行的最小入口
- API 最小基线测试已被纳入正式质量门禁
- DevFleet 不再需要猜测验收命令
