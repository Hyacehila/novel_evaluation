# 领域模型

本文档定义小说智能打分系统的核心业务对象。

## 核心对象

### 1. 稿件 `Manuscript`

表示用户提交的待评分内容。

建议属性：

- 文本正文
- 标题
- 输入类型（开篇、章节、大纲、其它）
- 来源（直接输入、文件上传、历史记录）
- 语言或文体信息

### 2. 评测任务 `EvaluationTask`

表示一次独立的评测请求。

建议属性：

- 任务标识
- 输入稿件引用
- 评分模式
- Prompt 版本
- Provider 标识
- Schema 版本
- 执行状态

### 3. 评分结果 `EvaluationResult`

表示面向用户返回的结构化评分结果。

建议包含：

- 顶层评分
- 平台匹配结果
- 编辑结论
- 市场判断
- 详细分析
- 优势与弱点列表

### 4. 评分维度 `ScoreDimension`

表示系统关注的核心评分维度。

当前已确认至少包含：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

### 5. 平台匹配 `PlatformRecommendation`

表示作品与平台的匹配建议。

建议包含：

- 平台名称
- 匹配百分比
- 匹配原因

### 6. 评测记录 `EvalRecord`

表示一次评测执行及其比较结果。

建议包含：

- 样本引用
- 使用的 Prompt 版本
- 使用的 Provider
- 输出结构是否合法
- 与基线的差异
- 执行结论

## 边界原则

- 领域对象独立于具体前端框架
- 领域对象独立于具体模型供应商
- 领域对象是后续 Schema、Prompt、评测的共同基础
