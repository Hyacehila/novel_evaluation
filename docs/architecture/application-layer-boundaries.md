# 应用层边界说明

## 适用范围

- `apps/api/`
- `apps/worker/`
- `packages/application/`
- `packages/domain/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `packages/schemas/`
- `evals/`

## 核心原则

- API 负责 HTTP，不负责业务编排
- Application 负责用例与状态推进
- Provider adapter 负责模型调用归一化
- Prompt runtime 负责资产读取与选择
- `packages/schemas/` 是正式结构真源
- worker 不拥有用户任务主执行权

## 目录职责

### `apps/api`

负责：

- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`
- 进程内用户任务执行器

不负责：

- 拼接正式 Prompt
- 直接调用 Provider SDK
- 维护第二套状态机

### `apps/worker`

负责：

- `batch`
- `eval`
- report/baseline 写出

不负责：

- 接收用户主任务
- 发明新任务状态

### `packages/application`

负责：

- 创建任务
- 读取任务
- 读取结果
- dashboard/history 聚合
- 评分主线编排
- 失败与阻断路径收敛

### `packages/provider-adapters`

负责：

- `ProviderExecutionRequest/Success/Failure`
- 统一 `providerRequestId`
- 统一 `durationMs`
- 统一 `retryable`

### `packages/prompt-runtime`

负责：

- 读取 Markdown 正文
- 读取 YAML registry/version
- 根据冻结优先级选择 Prompt
- 提供 promptId/promptVersion 给 application

### `packages/schemas`

负责：

- input/output/stages/evals 正式结构
- 不负责 API 路径和前端 View Model

## 依赖方向

```text
apps/api -> packages/application
apps/worker -> packages/application

packages/application -> packages/prompt-runtime
packages/application -> packages/provider-adapters
packages/application -> packages/schemas
packages/application -> packages/domain

evals -> packages/application / packages/schemas
```

## 标准调用链

### 用户任务

`apps/web -> apps/api -> packages/application -> packages/prompt-runtime -> packages/provider-adapters -> packages/schemas -> apps/api`

### 回归任务

`apps/worker -> evals -> packages/application -> packages/prompt-runtime -> packages/provider-adapters -> packages/schemas`

## 明确越界

- 在路由里拼 Prompt
- 在 Provider adapter 里定义业务结果字段
- 在前端假契约里反向定义正式 schema
- 让 worker 自行决定用户主任务状态
