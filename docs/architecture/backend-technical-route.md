# 后端技术路线

## 技术路线结论

`Phase 1` 后端实现基线固定为：

- `Python 3.13 + uv`
- `FastAPI`
- `Pydantic`
- `SQLite`
- `DeepSeek API`
- `PocketFlow`

## 运行模型

- `apps/api` 是用户任务的唯一主入口
- `POST /api/tasks` 成功后创建 `queued` 任务
- API 进程内执行器推进用户任务
- `apps/worker` 只负责 `batch/eval`
- 本地状态只落在 `SQLite`

## 采用原因

### 本地单用户交付优先

当前目标是让用户在本机安装依赖、配置 API Key、启动 `web/api/worker` 后可运行，而不是优先服务公网高并发。

### 契约先行

后端已经冻结：

- API v0
- 任务状态与错误语义
- Provider 执行契约
- Prompt 资产格式
- 上传与摄取边界

技术路线必须服务这些契约，而不是重新把项目拉回技术中立状态。

## 组件职责

### `FastAPI`

- 提供 HTTP 路由
- 解析请求
- 组织依赖注入
- 返回统一 envelope

### `Pydantic`

- 表达边界 DTO
- 承担运行时校验
- 不替代 `packages/schemas/` 成为正式结构真源

### `SQLite`

- 持久化 `EvaluationTask`
- 持久化 `EvaluationResultResource`
- 持久化 `EvalRecord / EvalBaseline / EvalReport`
- 提供重启后读取能力

### `DeepSeek API`

- 当前唯一正式 Provider
- 通过 provider adapter 暴露，不直接泄漏 SDK

### `PocketFlow`

- 只负责执行链编排
- 不定义业务字段、状态枚举或 Prompt 真源

## 当前不采用

- 队列中间件作为主前提
- 分布式任务系统作为主前提
- API 直写 Provider SDK 的方式
- 前端直连模型 API 的方式
- 公网 SaaS 架构前提

## 关联真源

- 执行模型：`docs/architecture/runtime-execution-and-persistence.md`
- API：`apps/api/contracts/api-v0-overview.md`
- 状态与错误：`apps/api/contracts/job-lifecycle-and-error-semantics.md`
- Provider：`docs/contracts/provider-execution-contract.md`
