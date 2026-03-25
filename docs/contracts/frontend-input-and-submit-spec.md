# 前端输入与提交约束

## 文档目的

本文定义新建评测任务页中的输入对象、前端边界内校验范围、基础业务参数范围与提交规则，用于统一前端输入行为和后续联调口径。

## 核心原则

- 前端只做边界内校验，不替代后端校验
- 输入主线统一围绕联合投稿包模型
- 前端不提交 Prompt 正文、Prompt 版本或 Provider 内部策略
- 输入页只负责输入与提交，不负责任务执行或结果展示

## 首期输入对象

### 必需或条件必需字段

- `title`：稿件标题（必需）
- `chapters`：正文章节数组（与 `outline` 至少存在一侧）
- `outline`：大纲对象（与 `chapters` 至少存在一侧）
- `sourceType`：输入来源类型（必需）

### 派生字段

以下字段由前端或后端根据输入内容派生，不作为独立业务主输入：

- `inputComposition`
  - `chapters_outline`
  - `chapters_only`
  - `outline_only`
- `evaluationMode`
  - `full`
  - `degraded`

## 首期基础业务参数

首期基础业务参数明确到字段级，仅包括：

- `sourceType`

说明：

- `sourceType`：例如 `direct_input`、`file_upload`、`history_derived`
- `inputComposition` 与 `evaluationMode` 属于联合投稿包的派生语义，不应替代输入对象本身

以下内容不属于首期基础业务参数：

- Prompt 正文
- Prompt 版本选择
- Provider 内部策略
- 模型内部执行参数

## 输入来源规则

### 直接输入

- 用户直接粘贴或输入章节正文与/或大纲内容
- 属于正式输入来源

### 文件上传

- 用户上传支持的文本文件
- 前端只承接上传与基础文件信息
- 文件解析与正式内容提取仍由后端能力承接

## 前端边界内校验

前端可校验：

- `title` 是否为空
- `chapters` 与 `outline` 是否至少存在一侧
- 已填写的章节正文或大纲内容是否为空串
- 文件是否上传失败
- 单侧输入时是否需要提示其属于 `degraded` 评估

前端不负责：

- 结果结构校验
- 深层业务校验
- Prompt 相关校验
- Provider 相关校验

## 提交规则

### 提交前

必须满足：

- 存在有效 `title`
- `chapters` 与 `outline` 至少存在一侧
- 前端边界校验通过

### 提交后

- 后端返回任务标识时，前端进入 `任务详情 / 状态页`
- 若提交失败，前端停留在输入页并展示错误信息

## 页面职责边界

新建评测任务页：

- 负责采集联合投稿包输入
- 负责基础校验
- 负责提交任务

不负责：

- 管理任务执行状态
- 管理结果可读性
- 展示正式结果

## 与其他文档的关系

- 页面规格见 `docs/planning/frontend-page-specs.md`
- 前后端边界见 `docs/contracts/frontend-backend-boundary.md`
- 输入草稿模型见 `docs/contracts/frontend-view-models.md`
- 状态流见 `docs/architecture/frontend-task-and-state-flow.md`
