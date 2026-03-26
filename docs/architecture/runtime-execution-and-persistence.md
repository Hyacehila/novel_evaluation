# 运行时执行与持久化

## 文档目的

本文档冻结 `Phase 1` 的运行时执行模型、任务推进方式、持久化边界和重启语义。

## 冻结结论

- 本地状态存储固定为 `SQLite`
- 默认数据库路径固定为 `./var/novel-evaluation.sqlite3`
- 环境变量覆盖固定为 `NOVEL_EVAL_DB_PATH`
- 用户任务由 `apps/api` 进程内执行器推进
- `apps/worker` 不承接用户提交任务，只运行批处理与回归

## 持久化对象

`Phase 1` 至少持久化以下对象：

- `EvaluationTask`
- `EvaluationResultResource`
- `EvalRecord`（以 `evals/reports/{reportId}.records.json` 形式写出）
- `EvalBaseline`（以 `evals/baselines/{baselineId}.json` 形式写出）
- `EvalReport`（以 `evals/reports/{reportId}.json` 形式写出）

说明：

- `EvaluationResult` 正文作为 `EvaluationResultResource.result` 的一部分持久化
- Prompt/Schema/Provider 版本元信息必须随任务和回归记录保留
- `EvalRecord / EvalBaseline / EvalReport` 不进入用户任务 SQLite

## 用户任务执行模型

### 创建

- `POST /api/tasks` 成功后先创建 `queued` 任务
- 创建成功返回 `201`
- 每次成功创建都生成新的 `taskId`

### 推进

- API 进程内执行器负责把任务从 `queued` 推进到 `processing`
- 执行器负责运行正式评分主线
- 执行完成后进入：
  - `completed + available`
  - `completed + blocked`
  - `failed + not_available`

### 非幂等边界

- `POST /api/tasks` 明确定义为非幂等
- 重复提交会创建新任务
- Provider 内部重试不得创建第二个任务或第二份结果

## worker 职责边界

`apps/worker` 在 `Phase 1` 只负责：

- 批处理
- 回归执行
- baseline comparison
- 结构化 report 生成

`apps/worker` 不负责：

- 承接用户页面提交的主任务
- 定义任务状态机
- 作为用户主链路的唯一执行入口

## 重启语义

- 进程重启后，所有遗留 `processing` 任务统一转为 `failed + not_available`
- 失败错误码应映射为受控技术失败
- `Phase 1` 不做自动恢复执行
- 用户若需重试，应重新发起新任务

## 存储与恢复要求

- `SQLite` 文件必须被视为本地状态真源
- 历史列表读取必须基于持久化数据，而不是内存态
- 重启后 `GET /api/tasks/{taskId}`、`GET /api/tasks/{taskId}/result`、`GET /api/history` 仍可读取已完成资源

## 与其它文档的关系

- 范围边界见 `docs/planning/mvp-phase-1-scope.md`
- API 语义见 `apps/api/contracts/api-v0-overview.md`
- 状态与错误见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 本地配置见 `docs/operations/runtime-configuration-and-diagnostics.md`
