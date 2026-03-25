# API v0 总契约说明

## 文档角色

本文档冻结 `API v0` 的资源边界、接口职责、响应 envelope 和 HTTP 语义，用于支撑：

- `apps/api/` 路由设计
- 前端 Mock / adapter 开发
- `packages/application/` 用例输入输出对齐
- DevFleet 后续实现 mission 的 API 真源引用

本文档不替代：

- 正式 schema 文件
- 任务状态机主文档
- 前端页面 View Model
- 数据库存储设计

## 版本范围

当前阶段定义为 `API v0`，含义是：

- 用于仓库内部实现基线与本地协作
- 资源语义必须稳定
- 在进入更公开的版本治理前，仍允许做有限但受控的调整

## 当前运行假设

- 项目定位为开源项目、本地部署、本机联调
- `Phase 1` 以本地单用户可用为前提
- 当前不把公网鉴权、多租户和权限系统作为 `DevFleet-Ready` 阻塞项
- 但接口对象应避免写死未来无法扩展的认证假设

## API 设计原则

- 资源优先，路径使用名词而非动作
- 任务对象与结果对象分离
- 状态语义和错误语义显式化
- 对外结果必须是严格 JSON
- 前端不消费未校验的原始模型输出
- 聚合摘要接口只服务页面，不反向定义领域主对象
- 正式输入以联合投稿包模型为中心

## Base Path

统一前缀：

```text
/api
```

说明：

- 当前不额外引入 `/v0`
- 如未来进入公开 API 版本治理，可再显式化路径版本

## 通用响应 Envelope

### 成功响应

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": null
}
```

### 失败响应

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "服务暂时不可用"
  },
  "meta": null
}
```

### 统一约束

- `success=true` 时，`error` 必须为 `null`
- `success=false` 时，`data` 必须为 `null`
- `meta` 只用于分页、游标和辅助元信息
- 不允许返回“看起来成功但实际失败”的混合语义对象

## 错误对象

最小错误对象字段：

- `code`
- `message`

可选扩展字段：

- `details`
- `fieldErrors`
- `retryable`

说明：

- 用户可见错误不泄露内部堆栈、SDK 细节、密钥或原始异常
- 具体错误码含义以 `apps/api/contracts/job-lifecycle-and-error-semantics.md` 为准

## 核心资源模型

### 1. `EvaluationTask`

最小字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `hasChapters`
- `hasOutline`
- `evaluationMode`
- `status`
- `resultStatus`
- `resultAvailable`
- `errorCode`
- `errorMessage`
- `createdAt`
- `startedAt`
- `completedAt`
- `updatedAt`

字段约束：

- `resultAvailable=true` 当且仅当 `resultStatus=available`
- `status` / `resultStatus` 的合法组合必须服从状态语义主文档
- `errorCode` / `errorMessage` 在 `failed` 或 `blocked` 时必须可用

### 2. `EvaluationResultResource`

最小字段：

- `taskId`
- `resultStatus`
- `resultTime`
- `result`
- `message`

字段约束：

- `resultStatus=available` 时，`result` 必须是正式结果对象
- `resultStatus=not_available` 或 `blocked` 时，`result` 必须为 `null`
- `message` 用于补充当前结果资源语义，不替代结构化错误码

### 3. `EvaluationTaskSummary`

用于 `dashboard` 与 `history` 的摘要对象，最小字段：

- `taskId`
- `title`
- `inputSummary`
- `inputComposition`
- `status`
- `resultStatus`
- `resultAvailable`
- `createdAt`

### 4. `DashboardSummary`

包含：

- `recentTasks`
- `activeTasks`
- `recentResults`

### 5. `HistoryList`

包含：

- `items`
- `meta.nextCursor`
- `meta.limit`

## 路由总览

`API v0` 最小路由集合：

- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

## 路由详细说明

### 1. 创建任务

#### 路径

```text
POST /api/tasks
```

#### 职责

- 接收联合投稿包输入
- 执行请求边界校验
- 创建评测任务
- 返回任务标识与初始状态

#### 请求体最小语义

- `title`
- `chapters`
- `outline`
- `sourceType`

#### 边界约束

- `chapters` 与 `outline` 至少存在一侧
- 单侧输入允许创建任务，但应显式进入 `degraded` 语义
- 文件上传场景可采用 `multipart/form-data`
- 但业务语义必须与联合投稿包模型一致

#### 成功语义

- 返回 `201`
- 返回 `success=true`
- 返回最小任务对象
- 初始状态通常为 `queued + not_available`

#### 失败语义

- 请求边界错误时：
  - 返回失败 envelope
  - 不创建任务
- 任务创建成功后发生的后续失败，不在本接口中伪装成创建失败

### 2. 读取任务详情

#### 路径

```text
GET /api/tasks/{taskId}
```

#### 职责

- 返回单任务详情
- 返回执行状态与结果状态
- 返回最小联合输入语义
- 返回失败或阻断的结构化原因

#### 返回关注点

- `status`
- `resultStatus`
- `resultAvailable`
- `evaluationMode`
- `errorCode`
- `errorMessage`

#### 约束

- 已持久化的失败或阻断应表现为稳定资源状态，不重新包装为新的 `5xx`
- `taskId` 不存在时返回 `404`

### 3. 读取任务结果

#### 路径

```text
GET /api/tasks/{taskId}/result
```

#### 职责

- 返回正式结果资源
- 或返回结果当前不可用 / 被阻断的资源语义

#### 返回语义

- `available`：返回正式结果对象
- `not_available`：返回结果暂不可展示语义
- `blocked`：返回结果被阻断语义

#### 约束

- 仅在 `available` 时返回正式结果对象
- `not_available` 与 `blocked` 不允许返回伪结果
- `taskId` 不存在时返回 `404`
- 任务存在但结果不可读或被阻断时返回 `200`
- 结果资源的结构语义以 `docs/contracts/json-contracts.md` 为准

### 4. 读取工作台首页摘要

#### 路径

```text
GET /api/dashboard
```

#### 职责

- 为工作台首页提供摘要对象
- 降低首页联调复杂度

#### 返回关注点

- 最近任务摘要
- 处理中任务摘要
- 最近结果摘要

#### 约束

- 只返回摘要，不返回正式结果正文
- 聚合字段不得成为领域真源

### 5. 读取历史记录

#### 路径

```text
GET /api/history
```

#### Query 参数

- `q`
- `status`
- `cursor`
- `limit`

#### 职责

- 返回按任务组织的历史记录
- 支持最小搜索、筛选与分页

#### 约束

- 历史记录对象按任务摘要建模
- 不在该接口返回完整正式结果正文

## HTTP 状态码约定

### 成功状态码

- `200 OK`：读取成功
- `201 Created`：创建成功

### 失败状态码

- `400 Bad Request`：请求格式错误
- `404 Not Found`：任务或结果不存在
- `409 Conflict`：资源状态冲突
- `422 Unprocessable Entity`：语义合法但校验失败
- `429 Too Many Requests`：限流
- `500 Internal Server Error`：系统内部错误
- `502 Bad Gateway`：上游 Provider 异常
- `503 Service Unavailable`：服务暂不可用

说明：

- 读取已失败任务本身不应自动返回 `5xx`
- `5xx` 只用于当前请求本身失败，而不是历史资源状态失败

## 同步与异步语义

`Phase 1` 当前采用：

- 创建任务与读取状态分离
- 结果读取与任务读取分离
- 状态跟踪依赖 `Polling-First`
- 是否由 `worker` 执行不改变 API 资源语义

## 与其它真源的关系

- 正式结果字段语义见 `docs/contracts/json-contracts.md`
- 任务状态与错误语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 前端最小假契约见 `docs/contracts/frontend-minimal-api-assumptions.md`
- 领域对象语义见 `docs/architecture/domain-model.md`

## 完成标准

满足以下条件时，可认为 `API v0` 契约已足以支撑 DevFleet 后续开发：

- 前后端能围绕统一资源模型联调
- 成功、阻断、失败语义不再混写
- 任务对象、结果对象和摘要对象边界清晰
- 路由说明可以直接作为 API 实现 mission 的单一上游真源
