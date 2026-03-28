# 前端信息架构

## 文档定位

本文定义当前前端页面结构、核心对象、导航语义与可达性规则，以 `apps/web` 已落地的页面和路由为准。

本文不替代页面规格、状态流或字段契约，但会说明哪些页面已经实现、哪些仍只是未来保留概念。

## 当前架构基线

- 采用 `工作台主导式` 页面组织
- `任务详情 / 状态页` 与 `结果详情页` 分离
- 历史记录按任务组织
- 页面主要围绕“创建任务 -> 跟踪执行 -> 查看结果 -> 回访历史”展开
- `结果对比页` 目前没有实现路由，只保留未来扩展概念

## 当前页面树

```text
工作台首页
├─ 新建评测任务页
├─ 任务详情 / 状态页
│  └─ 结果详情页
└─ 历史记录页
```

## 当前已实现路由

```text
/
/tasks/new
/tasks/{taskId}
/tasks/{taskId}/result
/history
```

补充说明：

- `app/api/provider-status` 与 `app/api/provider-status/runtime-key` 是前端本地代理接口，不属于用户页面
- `/compare` 当前没有页面文件，也不在现有导航中

## 核心信息对象

### 1. 创建页本地草稿语义

新建页使用：

- `TaskCreateFormValues`
- 本地文件状态 `chaptersFile / outlineFile`
- `deriveDraftSemantics()`

共同表达提交前的本地编辑态以及 `inputComposition / evaluationMode` 派生结果。

### 2. 正式提交对象

- `JointSubmissionRequest`
- 前端 mutation 层的 `CreateTaskSubmissionRequest`

### 3. 评测任务

`EvaluationTask` 是任务流主对象，用于承载任务状态、输入摘要、运行元信息与结果可读性。

### 4. 结果资源与正式结果

- `EvaluationResultResource`：结果接口返回的资源壳
- `EvaluationResult`：`resultStatus=available` 时的正式结构化结果正文

### 5. 工作台与历史页对象

- `DashboardTaskSummaryView`
- `DashboardResultSummaryView`
- `HistoryListView`

历史页列表项直接复用 `DashboardTaskSummaryView`，没有单独的 `HistoryTaskItemView`。

### 6. Provider 状态对象

`ProviderStatusView` 用于前端展示 provider 当前是否可分析、配置来源以及是否允许在 UI 中录入运行时 key。

## 导航模型

### 一级导航

当前一级导航固定为：

- `工作台首页`
- `新建评测任务`
- `历史记录`

### 二级入口

- 首页最近任务 -> `任务详情 / 状态页`
- 首页最近结果 -> `结果详情页`
- 历史记录页任务项 -> `任务详情 / 状态页`
- 历史记录页结果按钮 -> `结果详情页`
- 任务详情页结果入口 -> `结果详情页`

### 非页面入口

- Provider 状态读取与运行时 key 配置通过本地代理接口进入，不提供独立页面

## 页面可达性规则

### 工作台首页

- 默认可达
- 承载最近任务、进行中任务与最近结果摘要

### 新建评测任务页

- 默认可达
- 是正式任务流起点

### 任务详情 / 状态页

- 只有在存在合法 `taskId` 时可达
- 读取失败时进入错误态，而不是伪造任务详情

### 结果详情页

- 路由可达，但只有 `resultStatus=available` 才进入正式结果阅读态
- `blocked`、`not_available`、`fetch_failed` 都展示语义态或错误态

### 历史记录页

- 默认可达
- 以任务为主列表，支持检索、状态筛选与游标分页

## 页面与对象映射

| 页面 | 主对象 | 页面职责 |
| --- | --- | --- |
| `工作台首页` | `DashboardSummaryView` | 展示最近任务、进行中任务、最近结果摘要 |
| `新建评测任务页` | `TaskCreateFormValues + deriveDraftSemantics()` | 采集输入、校验上传、创建任务 |
| `任务详情 / 状态页` | `TaskDetailView` | 展示任务状态、输入摘要、运行元信息与结果入口 |
| `结果详情页` | `ResultDetailView` | 展示 `overall + axes` 正式结果，或展示阻断 / 不可用态 |
| `历史记录页` | `HistoryListView` | 按任务组织历史记录并支持回访 |

## 任务完成后的导航规则

- 任务完成后默认停留在 `任务详情 / 状态页`
- 页面根据 `resultAvailable` 决定是否展示结果入口
- 当前不自动跳转到结果页

## 未来保留概念

### 结果对比页

- 当前仅作为未来扩展概念保留
- 现有代码未实现页面、路由和 feature
- 后续若落地，应在历史记录与结果元信息稳定后再接入

## 当前不纳入信息架构的内容

- Prompt 调试入口
- 模型调试入口
- 批量任务页
- 多角色后台管理页

## 与其他文档的关系

- 流程、状态与失败路径见 `docs/architecture/frontend-task-and-state-flow.md`
- 前后端职责边界见 `docs/contracts/frontend-backend-boundary.md`
- 页面消费对象见 `docs/contracts/frontend-view-models.md`
- 页面职责与展示规则见 `docs/planning/frontend-page-specs.md`
- 术语统一见 `docs/contracts/frontend-terminology.md`
