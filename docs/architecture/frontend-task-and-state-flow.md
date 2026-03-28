# 前端任务流与状态流

## 文档角色

本文档定义当前前端围绕评测任务的主流程、轮询策略、结果入口逻辑以及失败 / 阻断语义。

它是前端状态语义的主锚点，用于统一：

- 页面流转
- 查询与轮询节奏
- `status / resultStatus` 的消费规则
- 错误态、阻断态与不可用态

## 当前前提

- 前端直接联调真实 API
- 查询层基于 `@tanstack/react-query`
- `任务详情 / 状态页` 与 `结果详情页` 分离
- 本地 Next.js 代理只用于 provider 状态与运行时 key 配置
- 当前不引入鉴权和多租户

## 核心流程原则

- 主流程以任务为核心
- 任务完成后默认停留在任务页，由用户手动进入结果页
- 只有 `available` 结果才能进入正式结果正文路径
- `blocked`、`not_available`、`fetch_failed` 都只能展示语义态或错误态
- 摘要页与详情页职责分离

## 核心对象流转

```text
TaskCreateFormValues + 本地文件状态
-> deriveDraftSemantics()
-> CreateTaskSubmissionRequest
-> EvaluationTask
-> EvaluationResultResource
-> ResultDetailView
```

工作台与历史页分支：

```text
EvaluationTask
-> DashboardTaskSummaryView
-> HistoryListView
```

说明：

- 新建页本地草稿不再抽象为共享 `InputDraft`
- 历史页列表项复用 `DashboardTaskSummaryView`
- 结果页消费的是 `EvaluationResultResource -> ResultDetailView`，而不是直接读取原始结果 JSON

## 主流程

### 流程一：新建任务

1. 用户进入 `新建评测任务页`
2. 页面读取 `ProviderStatusView`
3. 用户填写正文 / 大纲或上传文件
4. `deriveDraftSemantics()` 派生 `inputComposition / evaluationMode`
5. 前端完成表单与上传校验
6. 提交创建请求
7. 后端返回 `taskId`
8. 前端跳转到 `任务详情 / 状态页`

### 流程二：任务执行中

1. `任务详情 / 状态页` 读取任务详情
2. 当 `status=queued|processing` 时，每 `2` 秒轮询一次
3. 页面展示输入摘要、输入组成、评测模式与运行元信息
4. 页面不读取正式结果正文

### 流程三：任务结束

1. 后端将任务置为终态
2. 前端停止任务轮询
3. 若 `completed + available`，任务页展示结果入口
4. 若 `completed + blocked`，任务页展示阻断说明
5. 若 `completed + not_available`，任务页保持终态但不展示结果入口
6. 若 `failed + not_available`，任务页展示失败说明

### 流程四：结果读取

1. `结果详情页` 先读取任务详情
2. 只有任务不是活动态时，才读取结果资源
3. `available` 展示正式 `overall + axes`
4. `blocked` 与 `not_available` 展示语义态说明
5. 结果资源读取失败时展示 `fetch_failed` 错误态

### 流程五：历史回访

1. 用户进入 `历史记录页`
2. 页面基于 `q/status/cursor/limit` 读取列表
3. 标题检索通过本地 debounce 同步到 URL
4. 用户可进入任务页，且仅在 `resultAvailable=true` 时进入结果页

### 流程六：工作台摘要刷新

1. 首页读取 `DashboardSummaryView`
2. 当存在活动任务时，每 `15` 秒自动刷新
3. 最近结果卡片只显示总体评分与总体结论摘要

## 状态体系

### 输入与提交状态（前端本地）

| 状态 | 含义 |
| --- | --- |
| `editing` | 用户正在编辑输入 |
| `validation_failed` | 表单或上传校验失败 |
| `submitting` | 创建任务请求提交中 |
| `submit_failed` | 创建任务请求失败 |

### 任务状态（后端真源）

| 状态 | 含义 |
| --- | --- |
| `queued` | 任务已创建，等待执行 |
| `processing` | 任务执行中 |
| `completed` | 任务执行链路结束 |
| `failed` | 任务执行链路失败 |

### 结果状态（后端真源）

| 状态 | 含义 |
| --- | --- |
| `available` | 存在可展示的正式结果正文 |
| `not_available` | 当前不存在正式结果正文 |
| `blocked` | 任务已结束，但结果被业务语义阻断 |

### 读取状态（前端本地）

| 状态 | 含义 |
| --- | --- |
| `fetch_failed` | 当前读取请求失败，不属于后端真源枚举 |

## 合法状态组合

前端当前依赖以下后端组合：

| `status` | `resultStatus` | 页面语义 |
| --- | --- | --- |
| `queued` | `not_available` | 等待执行 |
| `processing` | `not_available` | 执行中 |
| `completed` | `available` | 结果可读 |
| `completed` | `blocked` | 正常结束但结果被阻断 |
| `completed` | `not_available` | 正常结束但无可读结果资源 |
| `failed` | `not_available` | 技术失败 |

约束：

- `completed + not_available` 是允许出现的兼容读取状态
- `fetch_failed` 只表示本次网络 / 读取失败，不改写后端状态

## 输入与提交流程约束

创建页至少需要表达：

- `title`
- 文本输入或文件输入模式
- `chapters` 或 `outline` 至少一侧
- `inputComposition`
- `evaluationMode`

说明：

- 正式推荐输入为 `chapters + outline`
- `chapters only` 与 `outline only` 允许提交，但属于降级评测
- 上传模式只接受 `TXT / MD / DOCX`
- provider 不可分析时，创建页禁止发起任务创建

## 状态转移规则

### 输入阶段

```text
editing -> validation_failed
editing -> submitting
submitting -> submit_failed
submitting -> queued
```

### 任务阶段

```text
queued -> processing
queued -> failed
processing -> completed
processing -> failed
```

### 结果消费阶段

```text
completed + available -> 允许进入结果页
completed + blocked -> 结果页展示阻断态
completed + not_available -> 结果页展示不可用态
failed + not_available -> 停留任务页失败态
available -> fetch_failed
```

## 页面行为约束

### 新建评测任务页

- 承载 `editing`、`validation_failed`、`submitting`、`submit_failed`
- 读取 provider 状态并阻断不可分析时的提交
- 单侧输入时明确展示降级评测语义
- 不展示任务执行状态或正式结果正文

### 任务详情 / 状态页

- 承载 `queued`、`processing`、`completed`、`failed`
- 读取 `TaskDetailView`
- `queued / processing` 时轮询
- `completed + available` 时展示结果入口
- `completed + blocked` 时展示阻断说明
- `completed + not_available` 时展示终态元信息，但不展示结果入口
- `failed + not_available` 时展示失败说明

### 结果详情页

- 先确认任务已结束，再读取结果资源
- `available` 才进入正式结果阅读态
- `blocked`、`not_available`、`fetch_failed` 都不展示结果正文
- 正式正文围绕 `overall + axes` 展示

### 工作台首页与历史记录页

- 只展示摘要，不展示正式结果正文
- 首页自动刷新只在存在活动任务时开启
- 历史页通过 URL 保存检索、状态和游标

## 失败与阻断分类

| 类型 | 含义 | 主要停留页面 | 是否允许进入结果正文 |
| --- | --- | --- | --- |
| 输入校验失败 | 文本或上传未通过本地校验 | `新建评测任务页` | 否 |
| provider 未配置 | 当前 provider 无法分析，任务不能创建 | `新建评测任务页` | 否 |
| 提交失败 | 创建请求失败，任务未创建 | `新建评测任务页` | 否 |
| 任务失败 | 任务进入 `failed + not_available` | `任务详情 / 状态页` | 否 |
| 结果阻断 | 任务正常结束但结果被阻断 | `任务详情 / 状态页` 或 `结果详情页` | 否 |
| 结果不可用 | 任务结束但无可读结果资源 | `任务详情 / 状态页` 或 `结果详情页` | 否 |
| 结果读取失败 | 当前结果读取请求失败 | `结果详情页` | 否 |

## 空态、错误态与恢复入口

### 正常空态

以下属于正常空态：

- 工作台暂无最近任务
- 工作台暂无最近结果
- 历史记录检索无匹配项

### 错误态

- 工作台摘要读取失败
- 任务详情读取失败
- 结果资源读取失败
- 历史记录读取失败

### 恢复入口

- 工作台、任务页、结果页、历史页都提供显式重试
- 任务失败或阻断时，引导返回新建页重新提交

## 与其他文档的关系

- 页面结构见 `docs/architecture/frontend-information-architecture.md`
- 页面规格见 `docs/planning/frontend-page-specs.md`
- 查询策略见 `docs/contracts/frontend-api-consumption-and-query-strategy.md`
