# 前端术语对齐

## 文档目的

本文用于统一前端相关文档中的对象命名、页面命名、状态命名和展示术语，避免后续文档与实现阶段出现命名漂移。

## 页面命名

| 术语 | 统一写法 | 说明 |
| --- | --- | --- |
| 首页 | `工作台首页` | 不使用营销首页语义 |
| 新建页 | `新建评测任务页` | 正式任务流起点 |
| 任务页 | `任务详情 / 状态页` | 承载任务状态与任务过程 |
| 结果页 | `结果详情页` | 承载正式结构化结果 |
| 历史页 | `历史记录页` | 按任务组织 |
| 对比页 | `结果对比页` | 当前仅结构预留 |

## 对象命名

| 术语 | 统一写法 | 说明 |
| --- | --- | --- |
| 输入稿件 | `Manuscript` | 用户提交的联合投稿包对象 |
| 创建任务请求 | `JointSubmissionRequest` | 新建任务时的正式输入对象 |
| 任务 | `EvaluationTask` | 一次独立评测任务 |
| 结果 | `EvaluationResult` | 正式结构化结果 |
| 历史项 | `HistoryTaskItemView` | 历史记录页主列表对象 |
| 输入草稿 | `InputDraftView` | 前端编辑中的联合投稿包草稿 |

## 状态命名

### 输入与提交本地状态

- `editing`
- `validation_failed`
- `submitting`
- `submit_failed`

### 任务状态

- `queued`
- `processing`
- `completed`
- `failed`

### 结果状态

- `available`
- `not_available`
- `blocked`

### 读取失败本地派生状态

- `fetch_failed`

说明：

- `fetch_failed` 只属于前端页面本地派生状态
- `fetch_failed` 不是后端 `resultStatus` 或 `status` 枚举的一部分

## 输入组成术语

冻结统一写法：

- `chapters_outline`
- `chapters_only`
- `outline_only`

不再使用：

- `inputType`
- “开篇 / 章节 / 大纲 / 其它” 作为正式主输入枚举

## 展示术语

| 术语 | 统一写法 | 说明 |
| --- | --- | --- |
| 基础元信息 | `任务 ID / 创建时间 / 结果时间` | 首期显式展示 |
| 结果摘要 | `最近结果摘要` | 仅作为首页快捷入口 |
| 结果不可用 | `结果不可用` | 结果尚不能展示 |
| 结果阻断 | `结果被阻断` | 不允许按正式结果展示 |
| 任务失败 | `任务失败` | 任务执行未成功完成 |

## 使用规则

- 前端文档新增术语时，应优先复用本文现有术语
- 若需新增术语，应先判断是否属于页面、对象、状态、输入组成或展示五类
- 不要在不同文档中混用“评分任务 / 评测任务”“结果页 / 报告页”等并列称呼
- 不要把前端本地状态反向写回后端正式枚举

## 与其他文档的关系

- 页面命名应与 `docs/architecture/frontend-information-architecture.md` 保持一致
- 对象命名应与 `docs/architecture/domain-model.md` 和 `docs/contracts/frontend-view-models.md` 保持一致
- 状态命名应以 `docs/architecture/frontend-task-and-state-flow.md` 为唯一主锚点
