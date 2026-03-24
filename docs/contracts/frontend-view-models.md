# 前端页面数据视图模型

## 文档目的

本文定义前端页面消费的数据视图模型，用于在后端领域对象、正式 JSON 契约与前端页面之间建立稳定的中间层。

本文不替代正式 Schema，也不要求后端直接按本文的模型原样返回。前端可将后端契约结果映射为本文定义的视图对象。

## 设计原则

- 视图模型服务于页面消费，不等于领域模型
- 视图模型只包含页面真正需要的字段
- 首期显式展示只要求基础元信息
- Prompt、Schema、Provider 扩展字段可预留，但不作为首期强要求

## 视图模型总览

| 模型 | 主要页面 | 作用 |
| --- | --- | --- |
| `InputDraftView` | 新建评测任务页 | 表示用户正在编辑的输入草稿 |
| `DashboardTaskSummaryView` | 工作台首页 | 表示首页中的任务摘要 |
| `DashboardResultSummaryView` | 工作台首页 | 表示首页中的最近结果摘要 |
| `TaskDetailView` | 任务详情 / 状态页 | 表示单任务详情与状态信息 |
| `ResultDetailView` | 结果详情页 | 表示正式结果阅读对象 |
| `HistoryTaskItemView` | 历史记录页 | 表示历史任务列表项 |

## 1. InputDraftView

### 用途

用于承接新建评测任务页中的输入草稿。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示/使用 |
| --- | --- | --- | --- |
| `title` | 标题 | 可选 | 使用 |
| `text` | 正文输入 | 条件必需 | 使用 |
| `inputType` | 输入类型 | 必需 | 使用 |
| `sourceType` | 来源类型 | 必需 | 使用 |
| `attachmentName` | 上传文件名 | 可选 | 使用 |
| `attachmentType` | 上传文件类型 | 可选 | 使用 |

## 2. DashboardTaskSummaryView

### 用途

工作台首页的最近任务与处理中任务摘要。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示 |
| --- | --- | --- | --- |
| `taskId` | 任务 ID | 必需 | 是 |
| `title` | 任务标题或输入摘要标题 | 可选 | 是 |
| `inputType` | 输入类型 | 必需 | 是 |
| `status` | 任务状态 | 必需 | 是 |
| `createdAt` | 创建时间 | 必需 | 是 |
| `hasResult` | 是否存在可用结果 | 必需 | 是 |

## 3. DashboardResultSummaryView

### 用途

工作台首页中的最近结果摘要，作为快捷入口。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示 |
| --- | --- | --- | --- |
| `taskId` | 所属任务 ID | 必需 | 是 |
| `title` | 结果对应标题或摘要标题 | 可选 | 是 |
| `resultTime` | 结果时间 | 必需 | 是 |
| `signingProbability` | 核心评分摘要 | 可选 | 是 |
| `editorVerdict` | 简短结论摘要 | 可选 | 是 |

说明：

- 首页结果摘要只是快捷入口，不承担完整结果阅读功能。
- 首页结果摘要不改变“历史记录按任务组织”的原则。

## 4. TaskDetailView

### 用途

表示 `任务详情 / 状态页` 的核心消费对象。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示 |
| --- | --- | --- | --- |
| `taskId` | 任务 ID | 必需 | 是 |
| `title` | 标题或输入摘要标题 | 可选 | 是 |
| `inputSummary` | 输入摘要 | 可选 | 是 |
| `inputType` | 输入类型 | 必需 | 是 |
| `status` | 任务状态 | 必需 | 是 |
| `createdAt` | 创建时间 | 必需 | 是 |
| `errorMessage` | 错误信息 | 可选 | 是 |
| `resultAvailable` | 是否可进入结果页 | 必需 | 是 |

### 扩展字段预留

以下字段可预留，但首期不要求显式展示：

- `promptVersion`
- `schemaVersion`
- `providerId`

## 5. ResultDetailView

### 用途

表示 `结果详情页` 的正式结果阅读对象。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示 |
| --- | --- | --- | --- |
| `taskId` | 所属任务 ID | 必需 | 是 |
| `resultTime` | 结果时间 | 必需 | 是 |
| `signingProbability` | 签约概率 | 必需 | 是 |
| `commercialValue` | 商业价值 | 必需 | 是 |
| `writingQuality` | 写作质量 | 必需 | 是 |
| `innovationScore` | 创新分 | 必需 | 是 |
| `platforms` | 平台推荐列表 | 必需 | 是 |
| `marketFit` | 市场判断 | 必需 | 是 |
| `editorVerdict` | 编辑结论 | 必需 | 是 |
| `detailedAnalysis` | 详细分析对象 | 必需 | 是 |
| `strengths` | 优势列表 | 必需 | 是 |
| `weaknesses` | 弱点列表 | 必需 | 是 |
| `visualizationData` | 可视化数据 | 可选 | 条件展示 |

### 扩展字段预留

以下字段可预留，但首期不要求显式展示：

- `promptVersion`
- `schemaVersion`
- `providerId`
- `resultVersion`

## 6. HistoryTaskItemView

### 用途

历史记录页中的任务列表对象。

### 字段建议

| 字段 | 含义 | 必需性 | 首期展示 |
| --- | --- | --- | --- |
| `taskId` | 任务 ID | 必需 | 是 |
| `title` | 标题或输入摘要标题 | 可选 | 是 |
| `inputSummary` | 输入摘要 | 可选 | 是 |
| `inputType` | 输入类型 | 必需 | 是 |
| `status` | 任务状态 | 必需 | 是 |
| `createdAt` | 创建时间 | 必需 | 是 |
| `resultAvailable` | 是否可进入结果详情页 | 必需 | 是 |

## 显式展示规则

### 首期必须显式展示

- `taskId`
- `createdAt`
- `resultTime`
- 结果页所需核心评分与正式结果字段

### 首期可预留但不强制展示

- `promptVersion`
- `schemaVersion`
- `providerId`
- `resultVersion`

## 与正式契约的映射原则

- 结果页字段应围绕 `docs/contracts/json-contracts.md` 定义的正式结果结构映射
- 前端不得因为页面方便而重命名正式结果核心语义
- 前端可根据展示需要生成摘要字段，但不得改变正式结果含义

## 与其他文档的关系

- 页面作用见 `docs/planning/frontend-page-specs.md`
- 页面展示边界见 `docs/planning/frontend-page-specs.md`
- 输入边界见 `docs/contracts/frontend-input-and-submit-spec.md`
- 前后端职责边界见 `docs/contracts/frontend-backend-boundary.md`
