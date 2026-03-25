# 前端任务流与状态流

## 文档角色

本文档冻结前端围绕评测任务的主流程、页面停留点、状态命名、失败与阻断规则。

它是前端状态语义的主锚点，用于统一：

- 页面流转
- 轮询逻辑
- 结果入口逻辑
- 空态 / 错误态 / 阻断态
- 与后端状态真源的映射关系

## 当前前提

- 项目定位为开源项目、本地部署、本机联调
- `Phase 1` 以本地单用户可用为前提
- 前端继续采用 `Mock-First`、`Adapter-First`、`Polling-First`
- 当前不把鉴权和多租户作为进入前端联调的阻塞项

## 核心流程原则

- `Workflow-First`
- 主流程以任务为核心，而不是以结果页为唯一中心
- `任务详情 / 状态页` 与 `结果详情页` 分离
- 任务完成后默认由用户手动进入结果页
- 阻断结果和失败结果不能进入正式结果正文路径
- 摘要页与详情页职责分离

## 核心对象流转

```text
InputDraft -> JointSubmissionDraft -> EvaluationTask -> EvaluationResult -> HistoryTaskItem
```

说明：

- `InputDraft`：前端输入中的草稿态
- `JointSubmissionDraft`：可提交的联合投稿对象
- `EvaluationTask`：已提交、可轮询、可追踪的任务对象
- `EvaluationResult`：后端返回的正式结果正文
- `HistoryTaskItem`：历史记录页消费的任务摘要对象

## 主流程

### 流程一：新建任务

1. 用户进入 `新建评测任务页`
2. 用户填写正文与大纲
3. 前端完成边界内校验
4. 前端提交创建请求
5. 后端返回 `taskId`
6. 前端进入 `任务详情 / 状态页`

### 流程二：任务执行中

1. 前端轮询任务详情
2. 任务处于 `queued` 或 `processing`
3. 页面展示输入摘要、联合输入组成、评估模式和基础元信息
4. 页面不展示正式结果正文

### 流程三：任务结束

1. 后端将任务置为终态
2. 前端在 `任务详情 / 状态页` 感知终态
3. 若 `completed + available`，页面提供进入结果页入口
4. 若 `completed + blocked`，页面展示阻断说明
5. 若 `failed + not_available`，页面展示失败说明

### 流程四：历史回访

1. 用户进入 `历史记录页`
2. 以任务摘要查看历史项
3. 用户进入对应 `任务详情 / 状态页` 或 `结果详情页`

## 状态体系

### 输入与提交状态（前端本地）

| 状态 | 含义 |
| --- | --- |
| `editing` | 用户正在输入 |
| `validation_failed` | 输入未通过前端边界校验 |
| `submitting` | 任务正在提交 |
| `submit_failed` | 任务创建请求失败 |

### 任务状态（后端真源）

| 状态 | 含义 |
| --- | --- |
| `queued` | 任务已创建，等待执行 |
| `processing` | 任务执行中 |
| `completed` | 任务执行链路正常结束 |
| `failed` | 任务执行链路失败 |

### 结果状态（后端真源）

| 状态 | 含义 |
| --- | --- |
| `available` | 存在可展示的正式结果正文 |
| `not_available` | 当前不存在正式结果正文 |
| `blocked` | 任务正常结束，但结果被业务语义阻断 |

### 读取状态（前端本地）

| 状态 | 含义 |
| --- | --- |
| `fetch_failed` | 当前读取请求失败，不属于后端真源枚举 |

## 合法状态组合

前端只依赖以下合法后端组合：

| `status` | `resultStatus` | 页面语义 |
| --- | --- | --- |
| `queued` | `not_available` | 等待执行 |
| `processing` | `not_available` | 执行中 |
| `completed` | `available` | 结果可读 |
| `completed` | `blocked` | 正常结束但结果被阻断 |
| `failed` | `not_available` | 技术失败 |

约束：

- 不允许把 `completed + not_available` 当作长期稳定组合依赖
- `fetch_failed` 只表示本次网络/读取失败，不表示任务状态被改写

## 输入草稿约束

`JointSubmissionDraft` 至少需要表达：

- `title`
- `chapters`
- `outline`
- `inputComposition`

说明：

- 正式推荐输入为 `chapters + outline`
- `chapters only` 与 `outline only` 允许提交，但页面必须提示其属于降级评估
- 页面不再把 `opening`、`chapter`、`outline`、`other` 作为并列正式输入入口

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
completed + blocked -> 停留在任务页或阻断态
failed + not_available -> 停留在任务页失败态
available -> fetch_failed
```

## 页面行为约束

### 新建评测任务页

- 只承载 `editing`、`validation_failed`、`submitting`、`submit_failed`
- 不展示任务执行状态
- 不展示正式结果正文
- 页面应明确区分正文输入区与大纲输入区
- 单侧输入时应提示用户该任务会走降级评估

### 任务详情 / 状态页

- 主要承载 `queued`、`processing`、`completed`、`failed`
- 展示 `inputComposition`、`hasChapters`、`hasOutline`、`evaluationMode`
- `completed + available` 时展示结果入口
- `completed + blocked` 时展示阻断说明与返回入口
- `failed + not_available` 时展示失败说明与重试/返回入口
- 不使用伪结果替代任务状态说明

### 结果详情页

- 只有 `available` 才进入正式结果阅读态
- `not_available`、`blocked`、`fetch_failed` 都不进入正常结果正文
- 非法结果不得以“部分结果”“降级结果”的形式展示

### 工作台首页与历史记录页

- 只承载摘要展示态，不承载正式结果正文
- 空列表可作为正常空态
- 摘要不得替代任务页或结果页的正式语义

## 失败与阻断分类

| 类型 | 含义 | 主要停留页面 | 是否允许进入结果正文 |
| --- | --- | --- | --- |
| 输入校验失败 | 联合输入不满足前端边界 | `新建评测任务页` | 否 |
| 提交失败 | 创建请求失败，任务未创建 | `新建评测任务页` | 否 |
| 任务失败 | 任务进入 `failed + not_available` | `任务详情 / 状态页` | 否 |
| 结果不可用 | 任务仍在执行中 | `任务详情 / 状态页` | 否 |
| 结果阻断 | 任务正常结束但结果被阻断 | `任务详情 / 状态页` 或阻断态 | 否 |
| 结果读取失败 | 当前结果读取请求失败 | `结果详情页` 错误态 | 否 |

## 空态、错误态与恢复入口

### 正常空态

以下属于正常空态：

- 工作台暂无最近任务
- 工作台暂无最近结果摘要
- 历史记录页暂无历史任务
- 搜索或筛选后暂无匹配结果

### 非正常空态

以下不属于普通空态：

- 任务存在但读取失败
- 结果存在但读取失败
- 结果被阻断

### 恢复规则

- 输入错误：停留输入页，指向可修正问题
- 提交错误：停留输入页，允许重新提交
- 任务失败：停留任务页，不生成结果入口
- 结果读取失败：停留结果错误态，允许重试读取
- 结果阻断：只展示阻断说明、状态说明与返回入口

## 手动进入结果页规则

- 任务完成后默认停留在 `任务详情 / 状态页`
- 由页面提供结果入口
- 由用户手动进入 `结果详情页`
- 当前不把自动跳转结果页作为正式默认语义

## 与其他文档的关系

- API 消费假契约见 `docs/contracts/frontend-minimal-api-assumptions.md`
- 后端状态与错误语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 正式结果字段见 `docs/contracts/json-contracts.md`
- 页面规格见 `docs/planning/frontend-page-specs.md`

## 完成标准

满足以下条件时，可认为前端状态流文档已足以支撑 DevFleet 后续开发：

- 页面、adapter 和查询层对状态组合理解一致
- 阻断、失败、读取失败三类问题不再混淆
- 结果页只在正式可用结果存在时打开正文态
- 前端不会再自行发明第二套后端状态语义
