# 全 LLM 分阶段 Rubric 评分架构

## 目标

本文档定义小说智能打分系统的正式评分架构：以 `LLM as Judge` 为核心，采用“先做 `rubric` 分点评价，再由新模型聚合输出最终结果”的固定单主线流程。

该架构需要同时满足以下目标：

- 保持对外正式结果结构稳定
- 提高评分可解释性与可追踪性
- 让 Prompt、Schema 与 Evals 能围绕同一主线演进
- 避免并行评分路径、分叉升级与外部介入带来的额外治理复杂度
- 为后续运行时实现提供清晰、可冻结的阶段边界

说明：

- 本文档定义的是当前正式评分主线的架构约束
- 当前阶段仍以文档、契约与评测边界冻结为优先
- 本文档不要求立刻完成全部运行时实现

## 适用范围

当前一等公民输入对象：

- 小说开篇
- 章节节选
- 小说大纲

受限输入对象：

- 其它相关文本可进入 `other` 路径
- `other` 路径默认降低置信度预期，并允许更早进入不可评语义

当前阶段重点：

- 先定义单一正式主线
- 先冻结阶段职责与结构边界
- 不改变前端不得持有正式 Prompt 的治理原则
- 不改变正式输出必须为严格 JSON 的约束

## 核心原则

### 1. 单主线优先

系统只保留一条正式评分主线，不再保留带有成本分层和风险分流特征的并行路径设计。

### 2. 分点评价先于最终结论

最终输出必须建立在 `rubric` 分点评价结果之上，而不是由聚合模型直接绕过中间阶段整体直评。

### 3. 对外契约稳定，对内阶段分层

系统对外仍返回统一正式结果对象，但系统内部通过多个阶段对象承接预检查、分点评价、一致性整理、聚合与最终投影。

### 4. 证据嵌入评价项

不再将“证据抽取”定义为正式主线中的独立长期阶段。分点评价项本身必须携带对应文本依据、证据引用或观察说明。

### 5. 一致性能力保留为聚合前整理

一致性能力用于检查缺项、冲突、重复处罚、无依据结论等问题，但不再承担分叉升级、外部介入或额外路由职能。

### 6. 聚合模型只读取正式阶段结果

聚合模型的正式输入边界应是：

- `InputScreeningResult`
- `RubricEvaluationSet`
- `ConsistencyCheckResult`

聚合模型不应以原文全文作为正式主线依赖直接重做整体评分。

## Rubric 层次设计

### 一级维度

当前建议将内部 `rubric` 设计为“细粒度内部维度 + 稳定对外结果字段”的双层结构。

| 内部一级维度 | 说明 | 主要影响的对外字段 |
| --- | --- | --- |
| `marketAttraction` | 市场吸引力与签约潜力 | `commercialValue`、`signingProbability` |
| `narrativeExecution` | 叙事执行、信息组织与语言控制 | `writingQuality` |
| `characterMomentum` | 人物欲望、关系张力与情绪驱动 | `commercialValue`、`writingQuality` |
| `noveltyUtility` | 新鲜度、设定可用性与题材差异化 | `innovationScore` |
| `fatalRisk` | AI 味、套路污染、不可评与致命硬伤 | 顶层分数上限与风险标签 |

说明：

- 顶层四个分数继续保留为正式外部结果字段
- 内部一级维度不要求与外部字段一一对应
- `fatalRisk` 继续作为约束维度，而不是普通加权项

### 二级子维度建议

#### `marketAttraction`

- `hookStrength`：开场钩子是否能建立继续阅读动机
- `conflictContinuity`：冲突是否具有持续推进潜力
- `retentionPotential`：是否具备追更驱动力
- `platformFit`：内容调性与平台读者预期是否匹配

#### `narrativeExecution`

- `clarity`：叙述是否清楚、易读、不混乱
- `pacingControl`：节奏是否有效，是否出现拖沓或跳跃
- `informationOrganization`：信息投放是否有层次，是否说明书化
- `languageControl`：语言是否稳定，是否存在明显 AI 味与概念堆砌

#### `characterMomentum`

- `protagonistDrive`：主角欲望、目标与行动性是否成立
- `characterDifferentiation`：角色是否有辨识度
- `relationshipTension`：人物关系是否构成张力
- `emotionalTraction`：情绪推进是否能支撑阅读惯性

#### `noveltyUtility`

- `freshness`：核心卖点是否具有可感知的新鲜度
- `settingUsefulness`：设定是否真正服务叙事
- `themeControl`：题材混搭是否受控
- `differentiation`：与常见套路相比是否存在明确差异点

#### `fatalRisk`

- `aiManualTone`：明显 AI 教程腔、说明书腔、拼装感
- `staleFormula`：低级套路复制、低质爽点拼贴
- `conceptSpam`：术语轰炸、命名污染、系统面板污染
- `nonNarrativeSubmission`：输入并非可评的小说文本
- `insufficientMaterial`：文本长度、完整性或信息量不足

## 原子评分锚点

建议内部继续使用统一五档制，再映射到外部 `0-100` 区间。

| 档位 | 含义 |
| --- | --- |
| `0` | 不可评、严重失败或命中否决条件 |
| `1` | 明显薄弱，存在结构性问题 |
| `2` | 勉强成立，但缺陷显著 |
| `3` | 合格，可作为普通连载文本处理 |
| `4` | 明显突出，具备较强竞争力 |

分点评价项必须满足：

- 至少给出一个文本依据或证据引用
- 必须给出简短理由
- 必须包含置信度
- 如命中 `fatalRisk`，必须输出风险标签

## 正式评分主线

### 第 1 层：输入预检查

职责：

- 判断文本是否属于可评范围
- 判断输入类型更接近开篇、章节还是大纲
- 检查长度、完整性、可读性与基本语言异常
- 识别明显非小说文本或高噪声文本

输出：`InputScreeningResult`

约束：

- `rateable=false` 时优先进入结构化不可评路径
- 不可评应返回明确原因，而不是伪造低分结果

### 第 2 层：LLM Rubric 分点评价

职责：

- 按一级与二级 `rubric` 维度输出结构化评价项
- 每个评价项同时给出分档、理由、文本依据和风险标签
- 将“结论必须可追踪到依据”固化为正式阶段契约

输出：`RubricEvaluationSet`

约束：

- 分点评价项必须包含稳定的 `dimensionId` 与 `subdimensionId`
- 分点评价结果应同时覆盖正向维度与风险维度
- 无依据时不得直接输出高分

### 第 3 层：轻量一致性整理

职责：

- 检查分点评价结果是否缺项
- 检查维度之间是否存在明显冲突
- 检查是否存在重复处罚、无依据结论和空泛解释
- 为聚合模型提供更干净、可消费的中间结果

输出：`ConsistencyCheckResult`

约束：

- 本层只负责整理与冲突识别
- 本层不再承担额外升级、分流或外部介入职责

### 第 4 层：新模型聚合输出

职责：

- 读取预检查结果、分点评价结果和一致性整理结果
- 聚合生成一级维度总结和顶层分数草案
- 输出风险标签、强弱项、市场判断、编辑结论和详细分析草案
- 保证顶层字段之间的逻辑关系稳定

输出：`AggregatedRubricResult`

聚合原则：

- `commercialValue` 主要受 `marketAttraction` 影响，次级参考 `characterMomentum`
- `writingQuality` 主要受 `narrativeExecution` 影响，次级参考 `characterMomentum`
- `innovationScore` 主要受 `noveltyUtility` 影响，并受 `fatalRisk` 约束
- `signingProbability` 不应脱离前三项基础分独立飙升，并应受 `fatalRisk` 和一致性整理结果约束

### 第 5 层：正式结果投影

职责：

- 将聚合输出映射为稳定的正式结果对象
- 保留支持内部追踪的来源映射关系
- 对最终结果执行结构校验与正式输出约束检查

输出：`FinalEvaluationProjection`

说明：

- `FinalEvaluationProjection` 属于后端内部最后一步
- 对外 API 返回体仍应以正式输出 Schema 为唯一真源

## Prompt 与 Schema 映射

### Prompt 建议分层

建议将正式 Prompt 资产收敛为以下阶段类型：

- `screening`：输入预检查 Prompt
- `rubric_scoring`：分点评价 Prompt
- `aggregation`：聚合输出 Prompt
- `versions`：Prompt 版本记录
- `registry`：Prompt 元数据与启用规则

推荐目录落位：

- `prompts/scoring/screening/`
- `prompts/scoring/rubric/`
- `prompts/scoring/aggregation/`
- `prompts/versions/`
- `prompts/registry/`

### Schema 建议分层

后续正式结构建议沉淀到：

- `packages/schemas/input/`：输入预检查相关结构
- `packages/schemas/output/`：正式结果结构与投影结构
- `packages/schemas/evals/`：评测样本、报告与差异结构
- 评分中间对象可在内部契约目录中按阶段扩展

说明：

- 正式对外结果仍以最终输出 Schema 为唯一真源
- 中间阶段结构只作为后端内部契约维护，不直接暴露给前端作为正式业务接口

## 与现有输出契约的关系

当前系统对外继续保留以下顶层评分字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

新主线的目标不是替换这些字段，而是：

- 提高这些字段的生成过程可解释性
- 提高这些字段在 Prompt、Model 与版本变化下的稳定性
- 为 `strengths`、`weaknesses`、`platforms`、`marketFit`、`editorVerdict`、`detailedAnalysis.*` 提供更一致的来源

## 渐进落地建议

### Phase 1：冻结主线与词表

- 冻结一级维度与二级子维度词表
- 冻结正式阶段名称、顺序与职责
- 冻结对外字段与内部来源映射关系

### Phase 2：冻结阶段契约与 Prompt 资产边界

- 定义 `InputScreeningResult`
- 定义 `RubricEvaluationSet`
- 定义 `ConsistencyCheckResult`
- 定义 `AggregatedRubricResult` 与 `FinalEvaluationProjection`
- 补齐 `screening`、`rubric_scoring`、`aggregation` 的 Prompt 资产边界

### Phase 3：冻结 Evals 与运行时实现边界

- 将新主线接入回归评测口径
- 比较分点评价稳定性、聚合输出稳定性与最终结果漂移
- 再进入 API、应用层与 Worker 实现规划

## 成功标准

- 系统能解释每个顶层评分主要来自哪些内部维度与分点评价结果
- 系统只保留一条正式主线，不再存在双路径或仲裁阶段
- Prompt、Schema 与 Evals 围绕同一套 `rubric` 版本同步演进
- 对外正式结果结构保持稳定，不因内部架构调整而频繁变更
