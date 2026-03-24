# 前端最小 API 假设契约

## 文档定位

本文用于在后端尚未完整设计完成前，为前端提供一套可直接开工的最小 API 假设契约，用于：

- 本地 Mock
- 页面骨架开发
- 查询层与适配层开发
- 后续真实后端接入前的接口占位

本文不是最终正式 API 文档，也不替代 `packages/schemas/`。它的目标是让前端先稳定施工，并把未来返工尽量压缩在适配层。

## 使用原则

- 本文中的路径、字段与 envelope 是“前端当前实现假设”
- 后端后续即使调整具体路径或响应结构，也应优先通过适配层吸收差异
- 正式结果字段语义仍以 `docs/contracts/json-contracts.md` 和后续 `packages/schemas/` 为准
- 前端页面不直接绑定本文中的 DTO 结构，而应通过 mapper 转为 View Model

## 通用约定

### 路径前缀

当前前端默认假设业务接口前缀为：

```text
/api
```

说明：

- 这里只是前端当前实现假设
- 后端后续如采用不同前缀，可在 API client 层统一适配

### 字段命名

当前前端默认假设接口返回使用 `camelCase` 字段命名。

### 时间字段

当前前端默认假设时间字段使用 `ISO 8601` 字符串，例如：

```text
2026-03-24T10:30:00Z
```

### 标识字段

当前前端默认假设：

- `taskId` 为不透明字符串
- 前端不依赖其具体生成规则

## 通用响应 Envelope

当前前端默认假设所有业务接口都返回统一 envelope：

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

### 错误对象约定

建议最小错误对象包含：

- `code`
- `message`

必要时可扩展：

- `details`
- `fieldErrors`

## 前端当前采用的最小枚举假设

以下枚举值用于前端直接开工，不等于后端最终唯一方案。

### 输入类型 `inputType`

建议前端当前采用：

- `opening`
- `chapter`
- `outline`
- `other`

### 来源类型 `sourceType`

建议前端当前采用：

- `direct_input`
- `file_upload`
- `history_derived`

### 任务状态 `status`

当前与前端状态文档保持一致：

- `queued`
- `processing`
- `completed`
- `failed`

### 结果语义状态 `resultStatus`

当前最小假设为：

- `available`
- `not_available`
- `blocked`

说明：

- `fetch_failed` 是前端读取失败后的本地派生状态
- 不要求后端显式返回 `fetch_failed`

## 一、创建任务

### 路径

```text
POST /api/tasks
```

### 请求

#### 文本输入场景

```json
{
  "title": "测试开篇",
  "text": "小说正文内容",
  "inputType": "opening",
  "sourceType": "direct_input"
}
```

#### 文件上传场景

前端当前默认假设：

- 存在文件时可使用 `multipart/form-data`
- 其余结构字段与文本输入场景保持一致

### 成功响应

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260324_001",
    "status": "queued",
    "createdAt": "2026-03-24T10:30:00Z"
  },
  "error": null,
  "meta": null
}
```

### 失败响应示例

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入参数不合法",
    "fieldErrors": {
      "text": "正文不能为空"
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

### 成功响应

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260324_001",
    "title": "测试开篇",
    "inputSummary": "小说正文前 120 字摘要",
    "inputType": "opening",
    "status": "processing",
    "createdAt": "2026-03-24T10:30:00Z",
    "errorMessage": null,
    "resultAvailable": false,
    "resultStatus": "not_available"
  },
  "error": null,
  "meta": null
}
```

### 字段说明

最小任务详情对象建议包含：

- `taskId`
- `title`
- `inputSummary`
- `inputType`
- `status`
- `createdAt`
- `errorMessage`
- `resultAvailable`
- `resultStatus`

说明：

- `resultAvailable` 主要用于任务页是否展示结果入口
- `resultStatus` 用于任务页补充结果可用性语义
- 前端最小假契约应遵守：`resultAvailable = true` 当且仅当 `resultStatus = available`
- 当 `resultStatus = not_available` 或 `blocked` 时，`resultAvailable` 必须为 `false`

## 三、读取结果详情

### 路径

```text
GET /api/tasks/{taskId}/result
```

### 结果可用时的响应

```json
{
  "success": true,
  "data": {
    "taskId": "task_20260324_001",
    "resultStatus": "available",
    "resultTime": "2026-03-24T10:35:00Z",
    "result": {
      "signingProbability": 78,
      "commercialValue": 81,
      "writingQuality": 74,
      "innovationScore": 69,
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
        "plot": "情节推进较稳定",
        "character": "角色动机较清晰",
        "pacing": "节奏前中段略慢",
        "worldBuilding": "设定表达较完整"
      },
      "strengths": ["题材明确", "人物关系清晰"],
      "weaknesses": ["开篇冲突偏弱"],
      "visualizationData": null
    }
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
    "taskId": "task_20260324_001",
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
    "taskId": "task_20260324_001",
    "resultStatus": "blocked",
    "resultTime": null,
    "result": null,
    "message": "结果未满足正式展示条件"
  },
  "error": null,
  "meta": null
}
```

### 说明

- `result` 仅在 `resultStatus = available` 时存在
- `not_available` 与 `blocked` 均不应返回伪正式结果
- 若任务不存在，应返回 `404`
- 若任务存在但结果尚未生成、尚未就绪、当前不可展示或被阻断，应返回 `200` 且通过 `resultStatus` 表达语义
- 前端应基于 `resultStatus` 进入对应展示态

## 四、读取工作台首页摘要

### 路径

```text
GET /api/dashboard
```

### 成功响应

```json
{
  "success": true,
  "data": {
    "recentTasks": [
      {
        "taskId": "task_20260324_001",
        "title": "测试开篇",
        "inputType": "opening",
        "status": "processing",
        "createdAt": "2026-03-24T10:30:00Z",
        "hasResult": false
      }
    ],
    "activeTasks": [
      {
        "taskId": "task_20260324_001",
        "title": "测试开篇",
        "inputType": "opening",
        "status": "processing",
        "createdAt": "2026-03-24T10:30:00Z",
        "hasResult": false
      }
    ],
    "recentResults": [
      {
        "taskId": "task_20260320_003",
        "title": "另一篇测试稿",
        "resultTime": "2026-03-20T09:30:00Z",
        "signingProbability": 84,
        "editorVerdict": "有签约潜力"
      }
    ]
  },
  "error": null,
  "meta": null
}
```

## 五、读取历史记录

### 路径

```text
GET /api/history?q={query}&status={status}&cursor={cursor}&limit={limit}
```

### 参数说明

- `q`：搜索词，可为空
- `status`：任务状态筛选，可为空
- `cursor`：游标，可为空
- `limit`：分页大小

### 成功响应

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "taskId": "task_20260324_001",
        "title": "测试开篇",
        "inputSummary": "小说正文前 120 字摘要",
        "inputType": "opening",
        "status": "completed",
        "createdAt": "2026-03-24T10:30:00Z",
        "resultAvailable": true
      }
    ]
  },
  "error": null,
  "meta": {
    "nextCursor": null,
    "limit": 20
  }
}
```

## 推荐错误码最小集合

建议前端当前至少预留以下错误码映射：

- `VALIDATION_ERROR`
- `TASK_NOT_FOUND`
- `RESULT_NOT_AVAILABLE`
- `RESULT_BLOCKED`
- `INTERNAL_ERROR`

说明：

- 这些错误码用于前端错误态分类与文案映射
- `RESULT_NOT_AVAILABLE` 与 `RESULT_BLOCKED` 不是结果读取主路径的常态 envelope；主路径优先使用 `200 + data.resultStatus`
- 后端后续可以扩展，但不建议把错误语义全部塞进自然语言 message

## View Model 映射建议

前端不直接让页面消费上述 DTO。

建议映射方向如下：

- `POST /api/tasks` -> 跳转参数与初始任务状态
- `GET /api/tasks/{taskId}` -> `TaskDetailView`
- `GET /api/tasks/{taskId}/result` -> `ResultDetailView` 或结果错误态
- `GET /api/dashboard` -> `DashboardTaskSummaryView[]` + `DashboardResultSummaryView[]`
- `GET /api/history` -> `HistoryTaskItemView[]`

## 允许后续变化但不应扩散到页面层的内容

后续真实后端接入时，以下变化允许存在，但应优先通过适配层吸收：

- 路径前缀变化
- snake_case / camelCase 差异
- dashboard 聚合接口拆分
- 分页元信息结构变化
- 文件上传参数组织方式变化
- 错误 envelope 字段扩展

## 当前不包含的内容

本文当前不定义：

- 最终 OpenAPI 文档
- 最终鉴权方案
- 最终上传存储方案
- 对比页接口
- Prompt 版本与 Provider 扩展接口

## 与其他文档的关系

- 前后端边界见 `docs/contracts/frontend-backend-boundary.md`
- 输入边界见 `docs/contracts/frontend-input-and-submit-spec.md`
- 页面消费对象见 `docs/contracts/frontend-view-models.md`
- 查询策略见 `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- 正式结果语义见 `docs/contracts/json-contracts.md`
