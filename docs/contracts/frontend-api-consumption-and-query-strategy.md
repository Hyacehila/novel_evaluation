# 前端 API 消费与查询策略

## 文档定位

本文用于在后端尚未完整设计完成前，明确前端如何消费 API、如何组织查询与变更、如何管理轮询与缓存、如何把接口结果映射为页面可消费对象。

本文不替代正式 API 文档，也不替代正式 Schema。它的目标是让前端先有稳定的实现策略，而不是等待后端全部定稿后再开始开发。

## 核心结论

当前前端 API 消费基线为：

- 服务端状态统一使用 `TanStack Query` 管理
- 读取类操作使用 Query，创建类操作使用 Mutation
- 异步任务状态首期采用 `Polling-First`
- 页面不直接消费后端 DTO，而是先经过适配层映射为 View Model
- 页面不直接散落调用裸 `fetch`
- `fetch_failed` 属于前端读取失败后的本地派生状态，不要求后端显式返回

## 核心原则

### 1. 契约优先

前端只消费后端已经返回并满足当前最小契约的结构化数据：

- 不消费模型原始输出
- 不消费半结构化结果
- 不对非法结果做前端修复

### 2. Query / Mutation 分离

当前推荐：

- Query：读取 dashboard、task、result、history
- Mutation：创建任务

### 3. Polling-First

首期任务状态跟踪统一采用轮询策略，不把 `SSE` / `WebSocket` 作为进入开发的前置条件。

### 4. Adapter-First

页面层永远只依赖 View Model：

- 接口层返回 DTO
- 映射层把 DTO 转为 View Model
- 页面层消费 View Model

### 5. 不复制服务端状态

通过 Query 管理的数据，不再额外写入全局 store 作为第二份真相源。

## Query Key 建议

建议统一 Query Key：

- `dashboard-summary`
- `task-detail:{taskId}`
- `task-result:{taskId}`
- `history-list:{query}:{status}:{cursor}`

说明：

- Query Key 应包含足以唯一标识请求结果的参数
- 不建议把多个页面共享的不同请求强行挤进同一个 Key

## 页面级查询策略

## 一、工作台首页

### 目标

首页需要平衡展示：

- 最近任务摘要
- 处理中任务摘要
- 最近结果摘要

### 推荐策略

首期推荐将首页作为“聚合读取页面”：

- 前端优先消费一个 `dashboard` 聚合查询
- 由后端或 Mock 层一次性返回首页所需摘要数据
- 避免首页初期就拆成过多并行接口，增加联调复杂度

### 刷新策略

- 页面进入时立即读取
- 当首页存在 `queued` / `processing` 任务时，可启用轮询
- 建议轮询间隔：`15s`
- 当首页不存在处理中任务时，不必持续轮询

### 缓存策略

- `staleTime` 可设为 `30s`
- 回到首页时若数据仍新鲜，可直接复用缓存

## 二、新建评测任务页

### 目标

完成联合投稿包输入采集、边界校验与任务创建。

### 推荐策略

任务创建统一采用 Mutation：

- 页面提交时调用 `createTask`
- 成功后拿到 `taskId`
- 立即进入 `任务详情 / 状态页`

### 成功后的失效策略

任务创建成功后，建议失效以下查询：

- `dashboard-summary`
- `history-list:*`

这样返回首页或历史页时可以看到新任务。

### 失败策略

- 任务创建失败仍停留在输入页
- 字段级错误优先回填到表单层
- 非字段级错误以页面级提交错误展示

## 三、任务详情 / 状态页

### 目标

用于读取任务状态并跟踪其从 `queued` / `processing` 向 `completed` / `failed` 的变化。

### 推荐策略

- 页面进入时立即读取 `taskDetail(taskId)`
- 当任务状态是 `queued` 或 `processing` 时启用轮询
- 建议轮询间隔：`5s`
- 当任务状态变为 `completed` 或 `failed` 时停止轮询

### 任务完成后的处理

当任务状态从处理中转为 `completed`：

- 当前页面保持停留在 `任务详情 / 状态页`
- 仅当 `resultStatus = available` 时展示结果入口
- 当 `resultStatus = not_available` 或 `blocked` 时，保留任务页说明或进入对应语义态入口
- 不自动跳转 `结果详情页`
- 可主动失效 `task-result:{taskId}`，为用户后续进入结果页做准备
- 同时失效 `dashboard-summary` 与 `history-list:*`

### 错误映射

- 请求失败：映射为任务页读取失败态
- `404`：映射为任务不存在
- `failed`：映射为任务失败态，不生成结果正文入口

## 四、结果详情页

### 目标

读取正式结构化结果，并在异常时展示语义正确的结果错误态或阻断态。

### 推荐策略

- 用户进入结果页时再发起 `taskResult(taskId)` 查询
- 首期默认不对结果页做持续轮询
- 若接口返回 `available`，进入正式结果阅读态
- 若接口返回 `not_available` 或 `blocked`，进入对应语义态

### 关于 `fetch_failed`

`fetch_failed` 不要求后端显式返回。

其实现语义为：

- 前端请求结果接口时发生网络失败、超时或服务异常
- 前端在页面层本地派生 `fetch_failed`
- 页面展示重试与返回入口

### 结果页重试策略

- 允许手动点击重试
- 不建议默认无限自动重试
- 若来自深链接访问且结果尚不可用，可展示说明并允许返回任务页

## 五、历史记录页

### 目标

按任务组织历史列表，并支持首期搜索与状态筛选。

### 推荐策略

- 页面进入时读取 `historyList`
- 搜索词与状态筛选进入 URL
- 搜索输入采用防抖
- 建议防抖时间：`400ms`
- 首期不做轮询

### 分页策略

历史记录页首期建议采用：

- 游标分页优先
- 或由后端返回最简分页元信息

原因是：

- 更适合任务历史持续增长的场景
- 可减少前后端在总数计算上的早期耦合

### 缓存策略

- `staleTime` 可设为 `30s ~ 60s`
- 条件变化时按新 Query Key 重新获取
- 创建任务或任务完成后允许统一失效历史列表

## 请求封装策略

前端请求层建议分为三层：

### 1. HTTP Client 层

负责：

- 统一请求函数
- 统一响应 envelope 解析
- 统一错误归一化
- 基础超时与 headers

### 2. Endpoint 层

负责：

- 调用具体接口
- 返回 DTO
- 不承担页面级展示逻辑

### 3. Mapper 层

负责：

- DTO -> View Model 映射
- 后端状态语义 -> 前端页面语义映射
- 空字段与可选字段的页面化收敛

## 页面与接口的推荐对应关系

| 页面 | Query / Mutation | 说明 |
| --- | --- | --- |
| `工作台首页` | `dashboardSummary` | 聚合读取首页摘要 |
| `新建评测任务页` | `createTask` | 创建任务 |
| `任务详情 / 状态页` | `taskDetail(taskId)` | 查询任务状态并轮询 |
| `结果详情页` | `taskResult(taskId)` | 读取正式结果 |
| `历史记录页` | `historyList(params)` | 读取按任务组织的历史列表 |

## 建议的失效策略

| 触发动作 | 需要失效的查询 |
| --- | --- |
| 创建任务成功 | `dashboard-summary`、`history-list:*` |
| 任务完成 | `dashboard-summary`、`history-list:*`、`task-result:{taskId}` |
| 手动刷新任务页 | `task-detail:{taskId}` |
| 手动刷新结果页 | `task-result:{taskId}` |

## 与 Mock 并行开发的策略

在后端未完成前，前端应保证：

- Query hook 不依赖真实后端才能存在
- Mock adapter 与真实 adapter 使用同一套 View Model 输出
- 页面组件不感知当前数据来自 Mock 还是真实接口

## 当前不采用的策略

首期不采用：

- `WebSocket` 作为状态流主方案
- `SSE` 作为进入实现前提
- 全局事件总线同步任务状态
- 页面直接解析原始响应
- 页面直接修复非法结果结构

## 与其他文档的关系

- 技术路线见 `docs/architecture/frontend-technical-route.md`
- 应用壳与模块边界见 `docs/architecture/frontend-app-shell-and-module-boundaries.md`
- 前后端职责边界见 `docs/contracts/frontend-backend-boundary.md`
- 最小假契约见 `docs/contracts/frontend-minimal-api-assumptions.md`
- 页面消费对象见 `docs/contracts/frontend-view-models.md`
- 状态语义见 `docs/architecture/frontend-task-and-state-flow.md`
