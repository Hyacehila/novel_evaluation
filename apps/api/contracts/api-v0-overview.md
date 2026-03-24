# API v0 总契约说明

## 文档目的

本文档定义小说智能打分系统 `API v0` 的对外接口边界，为后端实现、前端联调、Mock 数据和适配层开发提供统一依据。

本文档回答的问题是：

- `API v0` 暴露哪些资源
- 各接口的职责边界是什么
- 成功响应与失败响应如何统一表达
- 哪些语义属于 `Phase 1` 固定约束
- 哪些内容属于后续版本再扩展

本文档不负责：

- 替代正式 Schema 定义
- 替代任务状态机真源说明
- 替代前端页面消费模型
- 定义数据库实现方式

## 版本范围

### 为什么是 v0

当前项目处于结构建设与实现准备阶段，接口需要先满足：

- 前后端协作稳定
- 任务与结果语义稳定
- 为后续 `v1` 正式外部化版本预留空间

因此当前接口定义为 `API v0`，代表：

- 用于仓库内部实现基线和协作
- 语义需要稳定
- 但仍允许在进入更正式公开契约前完成有限调整

## API 设计原则

- 资源优先，路径使用名词而非动作
- 状态语义和错误语义显式化
- 正式结果必须以严格 JSON 契约为目标
- 前端不接收未校验的模型原始输出
- 任务对象与结果对象分离
- 聚合接口只服务于明确页面，不反向成为领域主对象真源

## 当前实现承接假设

- `API v0` 由 `apps/api` 承接实现
- HTTP 入口框架基线为 `FastAPI`
- 边界请求响应 DTO 与运行时校验基线为 `Pydantic`
- 这些实现技术不替代本文档对资源语义、状态语义和错误语义的定义权

## Base Path

`API v0` 统一使用：

```text
/api
```

说明：

- 当前不额外引入 `/v0` 路径前缀
- 版本语义由文档与实现阶段共同约束
- 如果未来进入公开版本治理，可再升级为显式路径版本

## 认证与鉴权假设

`Phase 1` 中：

- 文档先不冻结最终鉴权方案
- 但接口设计应预留认证扩展能力
- 当前重点是资源结构、状态语义、错误语义与结果契约

说明：

- 若接口暂时以开发态方式开放，不代表长期不鉴权
- 鉴权策略后续进入正式实现前可单独补充

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
- `meta` 用于分页、游标或辅助元信息
- 不允许返回“看起来成功但实际失败”的混合语义对象

## 错误对象

最小错误对象包含：

- `code`
- `message`

可选扩展：

- `details`
- `fieldErrors`
- `retryable`

说明：

- 用户可见语义优先使用 `message`
- 程序处理优先使用 `code`
- 复杂诊断信息不直接泄露为原始异常

## 核心资源模型

## 1. Evaluation Task

表示一次评测任务。

最小关注字段：

- `taskId`
- `status`
- `createdAt`
- `inputType`
- `title`
- `inputSummary`
- `resultAvailable`
- `resultStatus`
- `errorMessage`

### 字段一致性规则

为避免双字段漂移，`API v0` 约定：

- `resultAvailable = true` 当且仅当 `resultStatus = available`
- 当 `resultStatus = not_available` 或 `blocked` 时，`resultAvailable` 必须为 `false`
- 前端若同时消费两个字段，应以该一致性规则为准，不再自行推断第二套语义

## 2. Evaluation Result

表示任务完成后的正式结构化结果。

最小关注字段：

- `taskId`
- `resultStatus`
- `resultTime`
- `result`

其中 `result` 指向正式结果对象，正式字段语义由 `packages/schemas/` 维护。

## 3. Dashboard Summary

表示首页聚合摘要对象，包括：

- `recentTasks`
- `activeTasks`
- `recentResults`

说明：

- `dashboard` 是页面聚合视图，不是领域真源对象

## 4. History List

表示按任务组织的历史记录集合。

## 路由总览

`API v0` 最小路由集合：

- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

## 路由详细说明

## 1. 创建任务

### 路径

```text
POST /api/tasks
```

### 职责

- 接收用户输入
- 执行系统边界内输入校验
- 创建评测任务
- 返回任务标识与初始状态

### 请求体最小语义

- `title`
- `text`
- `inputType`
- `sourceType`

说明：

- 文件上传场景可在实现中采用 `multipart/form-data`
- 但业务语义仍应与文本输入场景保持一致

### 成功语义

- 返回 `success=true`
- 返回最小任务对象
- 任务状态初始值通常为 `queued`

### 失败语义

- 输入结构不合法：返回校验错误
- 系统无法创建任务：返回系统错误

## 2. 读取任务详情

### 路径

```text
GET /api/tasks/{taskId}
```

### 职责

- 返回单任务详情
- 返回任务状态
- 返回结果是否可用的最小语义

### 返回关注点

- 任务状态
- 结果可用性
- 基础元信息
- 失败信息

### 说明

- 此接口不返回正式结果正文
- 此接口是任务页状态展示真源

## 3. 读取任务结果

### 路径

```text
GET /api/tasks/{taskId}/result
```

### 职责

- 返回正式结果对象
- 或返回结果当前不可用 / 被阻断的语义

### 返回语义

- `available`：返回正式结果对象
- `not_available`：返回结果暂不可用说明
- `blocked`：返回阻断说明

### 约束

- 仅在 `available` 时返回正式结果对象
- `not_available` 与 `blocked` 不允许返回伪结果
- 当 `taskId` 不存在，或对应任务资源不存在时，应返回 `404`
- 当任务存在，但结果当前不可展示或被阻断时，应返回 `200` 且通过 `resultStatus` 明确语义

### `404` 与 `200` 的判定规则

应按以下方式区分：

- `404 Not Found`：任务不存在
- `200 + resultStatus=not_available`：任务存在，但当前没有可展示的正式结果，包括尚未生成、尚未就绪或当前阶段不提供正式结果正文
- `200 + resultStatus=blocked`：任务存在，但结果被正式阻断，不能作为正式结果返回

这样可以保证：

- 资源不存在与结果不可展示是两类不同语义
- 前端可以基于稳定规则决定进入“资源不存在”还是“结果语义态”

## 4. 读取工作台首页摘要

### 路径

```text
GET /api/dashboard
```

### 职责

- 为首页提供聚合摘要数据
- 降低首页初期联调复杂度

### 返回关注点

- 最近任务摘要
- 处理中任务摘要
- 最近结果摘要

### 说明

- 首页聚合接口服务于页面效率，不反向定义领域主对象

## 5. 读取历史记录

### 路径

```text
GET /api/history
```

### Query 参数

- `q`
- `status`
- `cursor`
- `limit`

### 职责

- 返回按任务组织的历史记录
- 支持最小搜索与状态筛选
- 支持分页读取

### 分页语义

优先采用：

- 游标分页

返回 `meta` 时至少应支持：

- `nextCursor`
- `limit`

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

## 幂等性规则

### 创建任务

- `POST /api/tasks` 默认视为非幂等
- 如后续需要支持幂等创建，应通过显式幂等机制引入，不应隐式假设

### 读取接口

- 所有读取接口都应保持幂等

## 同步与异步语义

`Phase 1` 默认采用：

- 创建任务与读取状态分离
- 结果读取与任务读取分离
- 状态跟踪依赖轮询

说明：

- 当前不要求长连接状态流
- 当前不把同步直返完整结果作为主方案

## 分页、筛选与排序

### 当前必须支持

- 搜索：`q`
- 状态筛选：`status`
- 游标分页：`cursor`、`limit`

### 当前不强制支持

- 多字段复杂排序
- 高级筛选表达式
- 复杂组合检索

## 与 Schema 的关系

- 文档描述的是接口语义和资源边界
- 正式请求/响应结构真源应位于 `packages/schemas/`
- `Pydantic` 可用于 API 边界与运行时校验，但不替代正式 Schema 真源
- 路由不能自行发明第二套正式字段定义

## 向后兼容与变更规则

以下变化可视为非破坏性变化：

- 新增可选字段
- 新增接口
- 新增 `meta` 字段中的附加项

以下变化视为破坏性变化：

- 删除已有字段
- 修改已有字段语义
- 修改路径结构
- 修改任务状态或结果状态枚举含义
- 修改统一 envelope 的核心字段规则

## 当前不包含的内容

本文当前不定义：

- 最终 OpenAPI 规范
- 最终鉴权实现方案
- 文件上传存储实现细节
- 对比页接口
- Prompt 版本显式管理接口
- Provider 管理接口

## 完成标准

满足以下条件时，可认为 `API v0` 契约已可用于开发：

- 前端可以按该文档构造 Mock 数据与 Adapter
- 后端可以按该文档开始路由设计
- 任务对象、结果对象、首页聚合对象、历史对象边界清晰
- 所有核心接口都具备统一成功/失败语义
- 结果不可用与阻断场景不会被错误包装为成功结果正文

## 与现有文档的关系

- 正式结果语义见 `docs/contracts/json-contracts.md`
- 前端最小假契约见 `docs/contracts/frontend-minimal-api-assumptions.md`
- 前后端边界见 `docs/contracts/frontend-backend-boundary.md`
- 页面查询策略见 `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- 任务状态与错误语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
