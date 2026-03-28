# 前端应用壳与模块边界

## 文档定位

本文描述当前 `apps/web` 的实际应用壳结构、模块分层与依赖边界，目标是让文档与现有 Next.js 实现保持一致，而不是继续停留在未落地的目录草案。

本文回答“前端工程现在是怎么组织的”，但不替代页面规格、状态流、前后端字段契约或 API 语义文档。

## 当前原则

- 仍按 `Workflow-First` 组织页面模块
- 路由入口只负责装配，不直接承接业务查询细节
- 页面层不直接消费原始 DTO，而是消费映射后的 View Model
- 共享层只保留真实复用能力，不收纳页面专属逻辑
- API 层负责隔离后端与本地代理细节

## 当前目录结构

```text
apps/web/
├─ app/
│  ├─ layout.tsx
│  ├─ error.tsx
│  ├─ loading.tsx
│  ├─ page.tsx
│  ├─ history/page.tsx
│  ├─ tasks/new/page.tsx
│  ├─ tasks/[taskId]/page.tsx
│  ├─ tasks/[taskId]/result/page.tsx
│  └─ api/
│     └─ provider-status/
│        ├─ route.ts
│        └─ runtime-key/route.ts
├─ src/
│  ├─ api/
│  │  ├─ client.ts
│  │  ├─ contracts.ts
│  │  ├─ hooks.ts
│  │  ├─ mappers.ts
│  │  └─ provider-route.ts
│  ├─ features/
│  │  ├─ dashboard/
│  │  ├─ history/
│  │  ├─ result-detail/
│  │  ├─ task-create/
│  │  └─ task-detail/
│  ├─ shared/
│  │  ├─ config/
│  │  ├─ hooks/
│  │  ├─ layouts/
│  │  ├─ lib/
│  │  ├─ providers/
│  │  └─ ui/
│  ├─ test/
│  └─ view-models/
│     └─ index.ts
└─ README.md
```

说明：

- `app/` 是 Next.js 路由入口层
- `app/api/provider-status/*` 是前端本地代理路由，用于转发 provider 状态读取与运行时 key 配置
- `src/features/` 按页面工作流组织
- `src/api/` 以文件级模块承接 DTO、请求、映射和查询 hook
- `src/view-models/index.ts` 是页面稳定消费对象的导出点
- `src/shared/` 收纳跨页面复用的布局、工具、Provider 与基础 UI

## 应用壳职责

当前应用壳负责：

- 路由入口与页面挂载
- 全局布局与导航壳
- 查询客户端 Provider 装配
- 全局错误页与加载页
- 与后端本地代理有关的 Next.js route handler

当前应用壳不负责：

- 直接写业务级查询组合
- 直接把 DTO 拼成页面展示结构
- 承载某个页面的专属状态分支
- 变成全局业务逻辑容器

## 分层边界

### 1. `app/`

职责：

- 定义页面路由
- 承接 URL 参数
- 装配页面级 feature 组件
- 承接全局 `layout / error / loading`

不负责：

- 直接请求后端业务接口
- 编写 DTO 到 View Model 的映射
- 堆叠复杂页面逻辑

### 2. `src/features/`

当前 feature 以页面为边界：

- `dashboard`
- `task-create`
- `task-detail`
- `result-detail`
- `history`

职责：

- 组织 query / mutation
- 处理页面状态分支
- 装配共享 UI
- 承接页面专属交互逻辑

说明：

- `task-create` 还包含 `submission.ts`，用于表单 schema、上传校验、创建请求构造和 `deriveDraftSemantics()`
- 当前仓库没有单独的 `compare` feature，也没有 `/compare` 页面实现

### 3. `src/api/`

#### `client.ts`

负责：

- 统一 HTTP 请求
- 响应 envelope 解包
- API 错误归一化

#### `contracts.ts`

负责：

- 保存前端读取的 DTO 与枚举
- 定义前后端交互所需的最小接口类型

#### `mappers.ts`

负责：

- 将 DTO 映射为 `src/view-models` 中的页面对象
- 隔离后端字段变化
- 将结果资源标准化为前端页面语义

#### `hooks.ts`

负责：

- 基于 `@tanstack/react-query` 组织查询和 mutation
- 定义任务、结果、历史、工作台与 provider 状态的 query key
- 封装自动轮询策略

#### `provider-route.ts`

负责：

- 处理前端本地代理到 API 的 provider 状态请求
- 配合 `app/api/provider-status/*` 路由处理运行时 key 配置入口

### 4. `src/view-models/`

当前实际导出对象为：

- `DashboardTaskSummaryView`
- `DashboardResultSummaryView`
- `DashboardSummaryView`
- `TaskDetailView`
- `AxisResultView`
- `OverallResultView`
- `ResultBodyView`
- `ResultDetailView`
- `HistoryListView`
- `ProviderStatusView`

说明：

- 历史页列表项复用 `DashboardTaskSummaryView`
- 新建任务页没有共享导出的 `InputDraftView`，而是使用本地 `TaskCreateFormValues + deriveDraftSemantics()`

### 5. `src/shared/`

#### `config/`

- 路由常量

#### `hooks/`

- `use-debounced-value.ts`

#### `layouts/`

- `app-shell.tsx`

#### `lib/`

- 格式化与状态标签工具
- 样式类名工具

#### `providers/`

- `query-provider.tsx`

#### `ui/`

- `badge.tsx`
- `button.tsx`
- `card.tsx`
- `states.tsx`

## 依赖方向

当前依赖方向保持为：

```text
app -> features -> api / view-models / shared
api -> view-models / shared
view-models -> api/contracts（类型层）/ shared
shared -> shared
```

约束：

- `app/` 只依赖 `features` 与 `shared`
- `features` 可以依赖 `api`、`view-models`、`shared`
- `api` 不依赖具体 feature
- `shared` 不依赖页面 feature
- feature 之间避免直接横向引用实现细节

## 页面与模块映射

| 页面 / 路由 | 对应 feature | 当前职责 |
| --- | --- | --- |
| `/` | `dashboard` | 展示最近任务、进行中任务、最近结果摘要 |
| `/tasks/new` | `task-create` | 输入采集、文件上传、provider 可用性校验、任务创建 |
| `/tasks/{taskId}` | `task-detail` | 任务轮询、状态展示、结果入口 |
| `/tasks/{taskId}/result` | `result-detail` | 结果资源读取、可用态 / 阻断态 / 不可用态展示 |
| `/history` | `history` | 标题检索、状态筛选、游标分页、历史回访 |

## 当前不建议的做法

- 在 `app/*/page.tsx` 中直接写请求、映射和所有 UI 状态分支
- 跳过 `mappers.ts` 让页面直接吃 DTO
- 把页面专属逻辑提早塞进 `shared/`
- 为尚未实现的页面提前创建完整 feature 骨架

## 与其他文档的关系

- 页面结构与导航语义见 `docs/architecture/frontend-information-architecture.md`
- 状态流见 `docs/architecture/frontend-task-and-state-flow.md`
- 查询策略见 `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- 页面消费对象见 `docs/contracts/frontend-view-models.md`
- 页面规格见 `docs/planning/frontend-page-specs.md`
