# 集成边界说明

## 文档目的

本文档定义 API、Application、Prompt runtime、Provider adapter、SQLite 持久化、worker 和 evals 之间的交互边界。

## 集成原则

- 所有用户请求统一从 API 进入
- 所有用户任务统一由 Application 编排
- 所有用户任务统一由 API 进程内执行器推进
- 所有回归与批处理统一由 worker/evals 驱动
- 所有正式结构统一回到 `packages/schemas/`
- 所有 Provider I/O 统一回到 provider contract

## 主数据流

### 用户任务流

```text
Frontend
-> API
-> SQLite 创建 queued task
-> API in-process executor
-> Application
-> Prompt Runtime
-> Provider Adapter
-> Schemas
-> SQLite 更新 task/result
-> API 提供 task/result/history 读取
```

### 回归流

```text
Worker
-> Evals Runner
-> Application
-> Prompt Runtime
-> Provider Adapter
-> Schemas
-> EvalRecord / EvalBaseline / EvalReport
```

## 模块边界

### Frontend <-> API

- 前端提交输入与上传文件
- 后端解析上传、创建任务、返回结构化资源
- 前端不消费未经校验的原始模型输出

### API <-> Application

- API 只传递通过边界校验的 DTO
- Application 不依赖 HTTP 协议细节

### Application <-> Prompt Runtime

- 输入：`stage`、任务上下文、版本约束
- 输出：`promptId`、`promptVersion`、渲染后的内容

### Application <-> Provider Adapter

- 输入：`ProviderExecutionRequest`
- 输出：`ProviderExecutionSuccess` 或 `ProviderExecutionFailure`

### Application <-> SQLite Repository

- 创建与更新 `EvaluationTask`
- 写入 `EvaluationResultResource`
- 读取 dashboard/history/task/result

### Worker/Evals <-> Production Assets

- 只复用正式 Prompt、Schema、Provider adapter
- 不反向定义生产语义

## 失败传播规则

- 请求边界错误：API 识别，不创建任务
- 业务阻断：Application 决定进入 `completed + blocked`
- 技术失败：Application 决定进入 `failed + not_available`
- provider failure：先在 adapter 层归一化，再由 Application 决定任务结论

## 可替换与不可替换

### 可替换

- Prompt 正文版本
- Provider 实现
- worker/eval runner 内部执行方式

### 不可替换

- 任务状态枚举
- 结果状态枚举
- 上传字段与错误码
- `SQLite` 作为 `Phase 1` 唯一本地状态真源
