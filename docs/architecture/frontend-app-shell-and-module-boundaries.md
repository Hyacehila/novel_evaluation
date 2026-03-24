# 前端应用壳与模块边界

## 文档定位

本文用于定义 `apps/web` 在进入实际开发时的应用壳结构、模块分层、目录建议、依赖方向与职责边界，确保前端在直接开工时不会把页面、接口、映射和共享能力混写在一起。

本文回答“前端工程怎么组织”，但不替代页面规格、状态流、前后端边界或正式 API 设计。

## 核心原则

- 以 `Workflow-First` 组织模块，而不是先按技术类型拆满仓库
- 页面入口负责挂载，不负责业务细节堆叠
- 页面层不直接消费原始接口 DTO
- 共享层只沉淀真实复用内容
- API 适配层负责隔离后端变化
- 特性模块之间避免横向直接耦合

## 应用壳定义

`apps/web` 的应用壳负责：

- 路由入口与布局层级
- 全局 Provider 装配
- 一级导航与公共页面壳
- 全局错误边界与基础装载壳
- 与业务无关的基础能力注入

应用壳不负责：

- 直接发起业务请求
- 直接拼装页面 View Model
- 承载某个页面的专属业务判断
- 成为“全局业务逻辑容器”

## 首期应用壳职责

首期应用壳建议只包含以下能力：

- 根布局 `layout`
- 一级导航
- 页面容器宽度与基础布局
- 查询客户端 Provider
- 全局错误边界
- 全局加载壳
- 全局 Toast/消息反馈容器（如需要）

## 推荐目录结构

建议 `apps/web` 采用如下结构：

```text
apps/web/
├─ app/
│  ├─ layout.tsx
│  ├─ error.tsx
│  ├─ loading.tsx
│  ├─ page.tsx
│  ├─ tasks/
│  │  ├─ new/page.tsx
│  │  └─ [taskId]/
│  │     ├─ page.tsx
│  │     └─ result/page.tsx
│  ├─ history/page.tsx
│  └─ compare/page.tsx
├─ src/
│  ├─ features/
│  │  ├─ dashboard/
│  │  ├─ task-create/
│  │  ├─ task-detail/
│  │  ├─ result-detail/
│  │  ├─ history/
│  │  └─ compare/
│  ├─ api/
│  │  ├─ client/
│  │  ├─ contracts/
│  │  ├─ mappers/
│  │  └─ mocks/
│  ├─ view-models/
│  ├─ shared/
│  │  ├─ ui/
│  │  ├─ layouts/
│  │  ├─ hooks/
│  │  ├─ lib/
│  │  ├─ config/
│  │  └─ constants/
│  └─ test/
└─ README.md
```

说明：

- `app/`：Next.js 路由入口层
- `src/features/`：按业务页面/流程组织的功能模块
- `src/api/`：接口请求、临时契约、映射、Mock
- `src/view-models/`：页面最终消费的稳定类型
- `src/shared/`：共享 UI 与基础工具
- `src/test/`：测试支撑层

## 各层职责边界

### 1. `app/`

用于承接路由与页面入口。

职责：

- 定义页面路径
- 承接路由参数
- 装配页面布局
- 挂载对应 feature container

不负责：

- 直接写业务查询逻辑
- 直接写 DTO 到 View Model 的映射
- 直接承载复杂页面结构

### 2. `src/features/`

用于承接页面级业务模块，是首期最重要的实现层。

建议每个 feature 围绕单一页面或单一工作流组织，例如：

- `dashboard`
- `task-create`
- `task-detail`
- `result-detail`
- `history`
- `compare`

每个 feature 内可按需要包含：

- `components/`
- `containers/`
- `hooks/`
- `schemas/`
- `utils/`
- `__tests__/`

但不要求每个目录都预先建立齐全。

### 3. `src/api/`

用于承接与后端交互相关的实现边界。

#### `client/`

负责：

- 统一 HTTP client
- 请求头/超时/通用错误包装
- 通用响应 envelope 解析

#### `contracts/`

负责：

- 保存当前前端基于最小假契约定义的 DTO
- 保存临时接口层类型

这里的 DTO 不等于页面直接消费的数据结构。

#### `mappers/`

负责：

- 将 DTO 映射为前端 View Model
- 将后端语义转成前端页面展示语义
- 将后端字段变化隔离在映射层

#### `mocks/`

负责：

- Mock 数据
- Mock handler
- 无后端阶段的假实现支撑

### 4. `src/view-models/`

用于保存前端页面稳定消费对象，对应：

- `InputDraftView`
- `DashboardTaskSummaryView`
- `DashboardResultSummaryView`
- `TaskDetailView`
- `ResultDetailView`
- `HistoryTaskItemView`

页面与 feature 应优先依赖这里的对象，而不是原始接口结构。

### 5. `src/shared/`

只承载跨 feature 的共享能力。

#### `ui/`

用于共享基础 UI：

- Button
- Input
- Select
- Card
- Badge
- Dialog
- Skeleton
- EmptyState
- ErrorState

#### `layouts/`

用于公共布局片段，例如：

- 页面壳
- 顶部导航
- 内容区容器

#### `hooks/`

只承载跨 feature 复用的 hooks，例如：

- `useDebouncedValue`
- `usePaginationParams`
- `useMounted`

不建议把页面专属业务 hooks 提前提升为 shared。

#### `lib/`

用于少量通用工具，例如：

- 日期格式化
- 安全字符串处理
- query string 工具

#### `config/` 与 `constants/`

用于：

- 环境变量封装
- 常量枚举
- 路由常量
- Query key 常量

## Feature 内部边界建议

建议 feature 采用“container + component + hook”分工：

### `containers/`

负责：

- 页面装配
- 组织多个 query / mutation
- 处理页面级状态分支

### `components/`

负责：

- 纯展示组件
- 低副作用的交互组件
- 接收 View Model 或明确 props

### `hooks/`

负责：

- 页面专属组合逻辑
- 查询组合逻辑
- URL 参数同步逻辑

### `schemas/`

负责：

- 页面表单的 `Zod` schema
- feature 内部校验规则

## 依赖方向

推荐依赖方向如下：

```text
app -> features -> api / view-models / shared
api -> shared
view-models -> shared（如仅依赖通用基础类型）
shared -> shared
```

约束如下：

- `app/` 可以依赖 `features` 与 `shared`
- `features` 可以依赖 `api`、`view-models`、`shared`
- `api` 不应依赖 `features`
- `shared` 不应依赖任何具体 feature
- 不建议 feature 之间直接互相导入实现文件

## 页面与模块映射

| 页面 | 推荐 feature | 主要职责 |
| --- | --- | --- |
| `工作台首页` | `dashboard` | 组织任务摘要、处理中任务、最近结果入口 |
| `新建评测任务页` | `task-create` | 输入表单、上传、前端边界校验、任务创建 |
| `任务详情 / 状态页` | `task-detail` | 任务状态查询、轮询、结果入口 |
| `结果详情页` | `result-detail` | 正式结果读取、阻断态与错误态 |
| `历史记录页` | `history` | 列表读取、搜索、状态筛选与回访 |
| `结果对比页` | `compare` | 当前只承接结构预留 |

## 不建议的组织方式

当前不建议：

- 把所有页面组件都堆在一个 `components/` 目录
- 在页面文件中直接发请求、映射数据、处理错误态和拼装全部 UI
- 让 `shared/` 演变为巨型杂物目录
- 引入过重的领域层抽象，导致前端在尚未实现前就先陷入架构分层负担
- 在无复用前提下过早抽象一堆“通用业务组件”

## 与后端尚未设计完成时的协作方式

在后端尚未落定前：

- 页面壳与 feature 可先实现
- `api/contracts` 可先按最小假契约建立 DTO
- `api/mappers` 可先把 DTO 映射为 View Model
- `api/mocks` 用于支撑本地页面开发
- 后续接入真实后端时，优先修改 `api/contracts` 与 `api/mappers`

## 与其他文档的关系

- 技术路线见 `docs/architecture/frontend-technical-route.md`
- 页面结构与导航语义见 `docs/architecture/frontend-information-architecture.md`
- 页面规格见 `docs/planning/frontend-page-specs.md`
- 查询策略见 `docs/contracts/frontend-api-consumption-and-query-strategy.md`
- 最小假契约见 `docs/contracts/frontend-minimal-api-assumptions.md`
- 页面消费对象见 `docs/contracts/frontend-view-models.md`
