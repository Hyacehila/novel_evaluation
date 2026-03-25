# 前端最小 API 假设契约

## 文档角色

本文档基于当前已落地的 `apps/api/src/api/routes.py`、`apps/api/src/api/errors.py` 与 `packages/schemas/`，为前端提供“现在真实可联调”的最小 API 消费假设。

它的目标不是补写未来接口，而是把当前仓库已经存在的最小后端事实收敛清楚，方便前端继续按 `Mock-First`、`Adapter-First`、`Polling-First` 开发。

## 使用原则

- 正式字段与枚举真源仍以 `packages/schemas/` 为准
- 本文只描述前端当前可稳定消费的最小运行事实
- 已规划但尚未落地的能力，不得反向写成当前运行接口事实
- 页面不直接绑定 DTO，应先经过 adapter / mapper 转为 View Model

## 当前已落地接口

当前仓库已落地的 API 读写入口只有：

- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/result`
- `GET /api/dashboard`
- `GET /api/history`

说明：

- 当前 `/api/history` 还没有公开查询参数、筛选参数和游标入参
- 当前没有鉴权、多租户和用户隔离语义
- 当前返回对象直接对应 `packages/schemas/output/` 中的结构模型

## 通用约定

### 路径前缀

```text
/api
```

### 字段命名

- 请求与响应字段使用 `camelCase`
- 路径参数名可在实现层使用 `task_id`，但前端语义仍按 `taskId` 理解

### 时间字段

- 时间字段使用 `ISO 8601` 字符串

### 标识字段

- `taskId` 为不透明字符串
- 前端不依赖其生成规则

## 通用响应 Envelope

当前后端使用：

- `SuccessEnvelope`
- `ErrorEnvelope`

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
    "code": "VALIDATION_ERROR",
    "message": "输入参数不合法",
    "details": null,
    "fieldErrors": {
      "title": "Field required"
    },
    "retryable": null
  },
  "meta": null
}
```

说明：

- `fieldErrors`、`details`、`retryable` 当前均为可选字段
- `422` 校验错误当前由 `apps/api/src/api/errors.py` 统一包装为 `VALIDATION_ERROR`

## 前端当前必须采用的最小枚举

### 输入组成 `inputComposition`

- `chapters_outline`
- `chapters_only`
- `outline_only`

### 来源类型 `sourceType`

- `direct_input`
- `file_upload`
- `history_derived`

### 评估模式 `evaluationMode`

- `full`
- `degraded`

### 任务状态 `status`

- `queued`
- `processing`
- `completed`
- `failed`

### 结果状态 `resultStatus`

- `available`
- `not_available`
- `blocked`

说明：

- `fetch_failed` 仍然只是前端本地派生状态，不属于后端正式枚举

## 合法状态组合

当前后端任务对象只允许以下组合：

- `queued + not_available`
- `processing + not_available`
- `completed + available`
- `completed + blocked`
- `failed + not_available`

约束：

- `resultAvailable = true` 当且仅当 `resultStatus = available`
- 不应把未出现在上述集合中的组合写成前端稳定依赖

## 一、创建任务

### 路径

```text
POST /api/tasks
```

### 请求体最小语义

当前请求对象直接对应 `JointSubmissionRequest`：

```json
{
  "title": "测试稿件",
  "chapters": [
    {
      "title": "第一章",
      "content": "章节正文内容"
    }
  ],
  "outline": {
    "content": "后续大纲规划内容"
  },
  "sourceType": "direct_input"
}
```

说明：

- `chapters` 与 `outline` 至少存在一侧
- 双侧齐备时为 `full`，单侧输入时会派生为 `degraded`
- 当前 API 路由本身尚未区分文件上传专用接口

### 成功响应

当前实现返回完整 `EvaluationTask`：

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260325_001",
    "title": "测试稿件",
    "inputSummary": "已提交 1 章正文和 1 份大纲",
    "inputComposition": "chapters_outline",
    "hasChapters": true,
    "hasOutline": true,
    "evaluationMode": "full",
    "status": "queued",
    "resultStatus": "not_available",
    "errorCode": null,
    "errorMessage": null,
    "schemaVersion": "1.0.0",
    "promptVersion": "prompt-v1",
    "rubricVersion": "rubric-v1",
    "providerId": "provider-local",
    "modelId": "model-local",
    "createdAt": "2026-03-25T00:00:00Z",
    "startedAt": null,
    "completedAt": null,
    "updatedAt": "2026-03-25T00:00:00Z",
    "resultAvailable": false
  },
  "error": null,
  "meta": null
}
```

说明：

- `provider-local` / `model-local` 是当前本地占位元数据，不代表正式外部 Provider 已接入

### 失败响应示例

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入参数不合法",
    "fieldErrors": {
      "body": "Value error, chapters 与 outline 至少存在一侧。"
    }
  },
  "meta": null
}
```

## 二、读取任务详情

### 路径

```text
GET /api/tasks/{taskId}
```

### 成功响应示例

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260325_001",
    "title": "测试稿件",
    "inputSummary": "已提交 1 章正文和 1 份大纲",
    "inputComposition": "chapters_outline",
    "hasChapters": true,
    "hasOutline": true,
    "evaluationMode": "full",
    "status": "processing",
    "resultStatus": "not_available",
    "errorCode": null,
    "errorMessage": null,
    "schemaVersion": "1.0.0",
    "promptVersion": "prompt-v1",
    "rubricVersion": "rubric-v1",
    "providerId": "provider-local",
    "modelId": "model-local",
    "createdAt": "2026-03-25T00:00:00Z",
    "startedAt": "2026-03-25T00:00:05Z",
    "completedAt": null,
    "updatedAt": "2026-03-25T00:00:05Z",
    "resultAvailable": false
  },
  "error": null,
  "meta": null
}
```

### `404` 响应示例

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "任务不存在"
  },
  "meta": null
}
```

## 三、读取结果详情

### 路径

```text
GET /api/tasks/{taskId}/result
```

### 结果可用时的响应

当前实现返回 `EvaluationResultResource`，其中 `resultTime` 同时出现在资源层与正式结果对象中：

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260325_001",
    "resultStatus": "available",
    "resultTime": "2026-03-25T00:10:00Z",
    "result": {
      "taskId": "task_20260325_001",
      "schemaVersion": "1.0.0",
      "promptVersion": "prompt-v1",
      "rubricVersion": "rubric-v1",
      "providerId": "provider-local",
      "modelId": "model-local",
      "resultTime": "2026-03-25T00:10:00Z",
      "signingProbability": 80,
      "commercialValue": 78,
      "writingQuality": 76,
      "innovationScore": 74,
      "strengths": ["题材明确"],
      "weaknesses": ["开篇冲突偏弱"],
      "platforms": [
        {
          "name": "女频平台 A",
          "percentage": 82,
          "reason": "题材匹配度较高"
        }
      ],
      "marketFit": "具备一定市场接受度",
      "editorVerdict": "可继续观察",
      "detailedAnalysis": {
        "plot": "情节推进稳定",
        "character": "角色动机明确",
        "pacing": "节奏略慢",
        "worldBuilding": "设定表达完整"
      }
    },
    "message": null
  },
  "error": null,
  "meta": null
}
```

### 结果暂不可用时的响应

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260325_001",
    "resultStatus": "not_available",
    "resultTime": null,
    "result": null,
    "message": "结果尚未生成或当前不可展示"
  },
  "error": null,
  "meta": null
}
```

### 结果被阻断时的响应

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260325_002",
    "resultStatus": "blocked",
    "resultTime": null,
    "result": null,
    "message": "结果未满足正式展示条件"
  },
  "error": null,
  "meta": null
}
```

## 四、读取工作台首页摘要

### 路径

```text
GET /api/dashboard
```

### 成功响应

当前实现返回 `DashboardSummary`：

```json
{
  "success": true,
  "data": {
    "recentTasks": [
      {
        "taskId": "task_20260325_001",
        "title": "测试稿件",
        "inputSummary": "已提交 1 章正文和 1 份大纲",
        "inputComposition": "chapters_outline",
        "status": "queued",
        "resultStatus": "not_available",
        "createdAt": "2026-03-25T00:00:00Z",
        "resultAvailable": false
      }
    ],
    "activeTasks": [],
    "recentResults": []
  },
  "error": null,
  "meta": null
}
```

## 五、读取历史记录

### 路径

```text
GET /api/history
```

### 成功响应

当前实现返回 `HistoryList`，并把 `meta` 同时放在 `data.meta` 与 envelope 顶层 `meta`：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "taskId": "task_20260325_001",
        "title": "测试稿件",
        "inputSummary": "已提交 1 章正文和 1 份大纲",
        "inputComposition": "chapters_outline",
        "status": "queued",
        "resultStatus": "not_available",
        "createdAt": "2026-03-25T00:00:00Z",
        "resultAvailable": false
      }
    ],
    "meta": {
      "nextCursor": null,
      "limit": 20,
      "extra": null
    }
  },
  "error": null,
  "meta": {
    "nextCursor": null,
    "limit": 20,
    "extra": null
  }
}
```

说明：

- 当前历史列表固定返回最近 `20` 条
- 搜索、状态筛选、游标入参仍属于规划能力，不是当前运行事实

## 当前已冻结但未全部发射的能力

以下能力可以继续保留在规划文档和前端 adapter 设计中，但当前不能写成后端已实现：

- 历史搜索与状态筛选入参
- 结果页自动轮询
- 鉴权与多租户
- 文件上传专用 API
- SDK 化查询封装

## 推荐错误码集合

前端当前应至少识别以下错误码：

- `VALIDATION_ERROR`
- `EMPTY_SUBMISSION`
- `INVALID_SOURCE_TYPE`
- `JOINT_INPUT_UNRATEABLE`
- `INSUFFICIENT_CHAPTERS_INPUT`
- `INSUFFICIENT_OUTLINE_INPUT`
- `JOINT_INPUT_MISMATCH`
- `RESULT_BLOCKED`
- `TASK_NOT_FOUND`
- `TASK_STATE_CONFLICT`
- `RESULT_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`
- `CONTRACT_INVALID`
- `RESULT_SCHEMA_INVALID`
- `STAGE_SCHEMA_INVALID`
- `PROVIDER_FAILURE`
- `TIMEOUT`
- `DEPENDENCY_UNAVAILABLE`
- `INTERNAL_ERROR`

说明：

- 不是所有错误码都已在当前路由层直接发射
- 但它们已经属于正式错误枚举冻结范围，前端不应自创第二套错误码体系

## View Model 映射建议

前端建议按以下方向吸收 DTO：

- `POST /api/tasks` -> 初始任务态与跳转参数
- `GET /api/tasks/{taskId}` -> `TaskDetailView`
- `GET /api/tasks/{taskId}/result` -> `ResultDetailView` 或结果阻断态
- `GET /api/dashboard` -> `DashboardTaskSummaryView[]` + `DashboardResultSummaryView[]`
- `GET /api/history` -> `HistoryTaskItemView[]`

## 与其他文档的关系

- API 主契约见 `apps/api/contracts/api-v0-overview.md`
- 状态与错误语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 正式结果语义见 `docs/contracts/json-contracts.md`
- 前端状态流见 `docs/architecture/frontend-task-and-state-flow.md`

## 完成标准

满足以下条件时，可认为本文档足以支撑当前前端联调：

- 前端知道当前真实存在哪些 API 入口
- 前端知道当前真实返回的 DTO 形状
- 已规划但未落地能力不再被误写成运行事实
- adapter 层可以在不反向发明后端真源的前提下继续开发
