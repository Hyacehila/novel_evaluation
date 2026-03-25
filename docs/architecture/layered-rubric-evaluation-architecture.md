# 面向网络小说的双输入全 LLM 分阶段 Rubric 评分架构

## 目标

本文档定义小说智能打分系统的正式评分架构：系统以 `LLM as Judge` 为核心，围绕“章节正文 + 后续大纲”的联合输入，采用“先做 `rubric` 分点评价，再由新模型聚合输出最终结果”的固定单主线流程。

该架构需要同时满足以下目标：

- 保持对外正式结果结构稳定
- 提高网络小说评估的解释性与可追踪性
- 让 Prompt、Schema、Evals 与运行时编排围绕同一主线演进
- 避免并行评分路径、`pairwise`、分叉升级与外部介入带来的额外治理复杂度
- 为后续开发提供可以直接落地的阶段边界与映射关系

## 适用范围

当前正式输入对象采用联合投稿包模型。

### 正式推荐输入

- `chapters`：作者上传的前几章节正文
- `outline`：作者上传的后续大纲规划

### 允许的降级输入

- 只有 `chapters`
- 只有 `outline`

说明：

- `chapters + outline` 是正式推荐输入形态
- `chapters only` 与 `outline only` 允许进入降级评估
- 降级评估必须显式降低部分维度置信度，不能假装信息完整

## 核心原则

### 1. 单主线优先

系统只保留一条正式评分主线，不保留并行评分路径、外部仲裁链路或 `pairwise` 支路。

### 2. 联合输入先于最终结论

最终输出必须建立在联合输入的分点评价结果之上，而不是将正文和大纲视作两个独立任务后再做松散拼接。

### 3. `pointwise` 先于整体结论

正式评分主线只保留 `pointwise` 分点评价：

- 不使用 `pairwise`
- 不使用候选比较式裁决
- 不让聚合层绕过中间阶段直接整体直评

### 4. 对外契约稳定，对内阶段分层

系统对外仍返回统一正式结果对象，但内部通过多个阶段对象承接：

- 输入预检查
- `LLM rubric` 分点评价
- 轻量一致性整理
- 新模型聚合输出
- 正式结果投影

### 5. 证据嵌入评价项

正式主线不再把“证据抽取”定义为独立长期阶段。每个评价项本身必须携带来源信息，并显式区分证据来自：

- `chapters`
- `outline`
- `cross_input`

### 6. 一致性能力聚焦跨输入冲突

一致性能力用于检查缺项、冲突、重复处罚、无依据判断，以及正文与大纲之间的承诺冲突，但不承担分叉升级与路由职责。

## Rubric 三层结构

正式评分内部采用三层结构：

1. 新 `8` 轴主评价层
2. 旧四维骨架层
3. 对外四分投影层

并额外保留 `fatalRisk` 作为跨层约束维度。

### 第一层：新 `8` 轴主评价层

| 轴 ID | 关注问题 | 主要证据来源 |
| --- | --- | --- |
| `hookRetention` | 开局是否能把读者留住，是否具备继续读的直接动力 | 以 `chapters` 为主 |
| `serialMomentum` | 连载推进惯性是否成立，后续是否有持续拉读者的动能 | `chapters` + `outline` |
| `characterDrive` | 主角欲望、行为驱动、人物关系张力是否成立 | `chapters` 为主 |
| `narrativeControl` | 叙事组织、信息投放、语言控制是否稳定 | 以 `chapters` 为主 |
| `pacingPayoff` | 节奏与兑现关系是否成立，铺垫与回报是否匹配 | `chapters` + `outline` |
| `settingDifferentiation` | 设定、题材组合与核心卖点是否有差异化且能被利用 | `chapters` + `outline` |
| `platformFit` | 内容调性与目标平台读者预期是否匹配 | `chapters` + `outline` |
| `commercialPotential` | 是否具备转化为持续连载商业表现的潜力 | `chapters` + `outline` |

说明：

- 新 `8` 轴是正式主评价层
- 这些轴直接服务网络小说投稿评估，不以文学评论为目标
- 每个轴都允许带有少量类型敏感性，但这种敏感性必须通过轻量标签条件化，而不是分叉流程

### 轻量标签机制

为支持常见网络小说类型差异，系统允许有限标签参与条件化判断，但必须保持简单、稳定、可治理。

建议标签：

- `primaryGenreTag`
- `secondaryGenreTags`
- `readerModeTag`

治理要求：

- 标签词表必须封闭
- 数量必须有限
- 标签只能影响少量提示与示例选择，不得改变主线结构
- 女频不再拆成额外独立复杂分支

### 第二层：旧四维骨架层

| 骨架维度 | 作用 |
| --- | --- |
| `marketAttraction` | 承接市场吸引、平台适配、追更动能与商业可跑性 |
| `narrativeExecution` | 承接叙事执行、节奏控制、信息组织与语言控制 |
| `characterMomentum` | 承接人物驱动、关系张力与情绪抓力 |
| `noveltyUtility` | 承接设定差异化、新鲜度与卖点可用性 |

说明：

- 旧四维继续保留，但不再是最上层主评价层
- 它们承担稳定骨架职责，帮助新 `8` 轴与最终四分衔接

### 第三层：对外四分投影层

系统对外继续保留以下正式字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

目标不是替换这些字段，而是让这些字段的来源更加稳定、可解释、可回归。

### 跨层约束：`fatalRisk`

`fatalRisk` 作为跨层约束维度保留，不并入新 `8` 轴加权。

建议风险项：

- `aiManualTone`
- `staleFormula`
- `conceptSpam`
- `fakePayoff`
- `nonNarrativeSubmission`
- `insufficientMaterial`

作用方式：

- 约束 `8` 轴判断上限
- 约束旧四维骨架层汇总
- 约束最终四分字段与是否可签结论

## 映射关系

### 新 `8` 轴 → 旧四维骨架层

| 新 `8` 轴 | 主归属骨架维度 | 次级影响 |
| --- | --- | --- |
| `hookRetention` | `marketAttraction` | `commercialPotential` 相关判断 |
| `serialMomentum` | `marketAttraction` | `narrativeExecution` |
| `characterDrive` | `characterMomentum` | `marketAttraction` |
| `narrativeControl` | `narrativeExecution` | `characterMomentum` |
| `pacingPayoff` | `narrativeExecution` | `marketAttraction` |
| `settingDifferentiation` | `noveltyUtility` | `marketAttraction` |
| `platformFit` | `marketAttraction` | `commercialPotential` |
| `commercialPotential` | `marketAttraction` | `characterMomentum` |

### 旧四维骨架层 → 对外四分字段

| 骨架维度 | 主要影响的对外字段 |
| --- | --- |
| `marketAttraction` | `commercialValue` |
| `narrativeExecution` | `writingQuality` |
| `characterMomentum` | `commercialValue`、`writingQuality` |
| `noveltyUtility` | `innovationScore` |

补充规则：

- `signingProbability` 建立在前三项基础分之上
- `platformFit` 对 `signingProbability` 有强约束
- `fatalRisk` 可以压低所有顶层字段，并在必要时触发不可签或不可评语义

## 原子评分锚点

建议内部继续使用统一五档制，再映射到外部 `0-100` 区间。

| 档位 | 含义 |
| --- | --- |
| `0` | 不可评、严重失败或命中否决条件 |
| `1` | 明显薄弱，存在结构性问题 |
| `2` | 勉强成立，但缺陷显著 |
| `3` | 合格，具备基础连载可读性 |
| `4` | 明显突出，具备较强竞争力 |

分点评价项必须满足：

- 至少给出一个证据引用
- 必须给出简短理由
- 必须给出置信度
- 必须标明证据来源类型
- 命中 `fatalRisk` 时必须输出风险标签

## 正式评分主线

### 第 1 层：输入预检查

职责：

- 判断联合输入是否可评
- 判断 `chapters` 与 `outline` 是否存在、是否足量、是否可读
- 识别输入组成是 `chapters_only`、`outline_only` 还是 `chapters_outline`
- 识别明显非小说文本、高噪声文本或结构失真文本
- 输出后续阶段所需的输入充分性与降级语义

输出：`InputScreeningResult`

约束：

- `rateable=false` 时优先进入结构化不可评路径
- 不可评应返回明确原因，而不是伪造低分结果
- 若只提供单侧输入，应显式标注降级评估状态

### 第 2 层：LLM Rubric 分点评价

职责：

- 按新 `8` 轴输出结构化评价项
- 允许每个评价项引用 `chapters`、`outline` 或跨输入观察
- 为每个评价项给出分档、理由、证据、风险标签与置信度
- 产出可被旧四维骨架层聚合消费的标准对象

输出：`RubricEvaluationSet`

约束：

- 分点评价项必须包含稳定的 `axisId`
- 无依据时不得直接输出高分
- 证据来源必须可追踪
- 类型条件化只能通过轻量标签与 examples 注入，不能改变主线结构

### 第 3 层：轻量一致性整理

职责：

- 检查分点评价是否缺项
- 检查正文与大纲之间是否存在明显承诺冲突
- 检查是否存在重复处罚、无依据结论和空泛解释
- 为聚合模型提供更干净、可消费的中间结果

输出：`ConsistencyCheckResult`

约束：

- 本层只负责整理与冲突识别
- 本层不承担额外升级、分流或外部介入职责

### 第 4 层：新模型聚合输出

职责：

- 读取预检查结果、`8` 轴分点评价结果和一致性整理结果
- 先汇总到旧四维骨架层，再投影到顶层四分字段草案
- 输出风险标签、强弱项、平台建议、市场判断与编辑结论草案
- 保持顶层字段逻辑关系稳定

输出：`AggregatedRubricResult`

聚合原则：

- `commercialValue` 主要受 `marketAttraction` 影响，次级参考 `characterMomentum`
- `writingQuality` 主要受 `narrativeExecution` 影响，次级参考 `characterMomentum`
- `innovationScore` 主要受 `noveltyUtility` 影响，并受 `fatalRisk` 约束
- `signingProbability` 不应脱离前三项基础分独立飙升，并应受 `platformFit`、`fatalRisk` 与一致性整理结果约束

### 第 5 层：正式结果投影

职责：

- 将聚合输出映射为稳定正式结果对象
- 保留支持内部追踪的来源映射关系
- 对最终结果执行结构校验与正式输出约束检查

输出：`FinalEvaluationProjection`

说明：

- `FinalEvaluationProjection` 属于后端内部最后一步
- 对外 API 返回体仍应以 `packages/schemas/` 为唯一真源

## Prompt 与 Schema 映射

### Prompt 建议分层

建议正式 Prompt 资产按以下阶段收敛：

- `input_screening`：联合输入预检查 Prompt
- `rubric_evaluation`：新 `8` 轴分点评价 Prompt
- `aggregation`：旧四维骨架汇总与最终结果草案 Prompt
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

- `packages/schemas/input/`：联合输入与输入预检查相关结构
- `packages/schemas/output/`：正式结果结构与投影结构
- `packages/schemas/evals/`：联合样本、报告与差异结构
- 评分中间对象在内部契约目录中按阶段扩展

说明：

- 正式对外结果仍以最终输出 Schema 为唯一真源
- 中间阶段结构只作为后端内部契约维护，不直接暴露给前端作为正式业务接口

## 成功标准

- 系统能解释每个顶层评分主要来自哪些 `8` 轴与骨架维度
- 系统能处理 `chapters + outline` 的联合输入，并显式识别单侧输入降级
- 系统只保留一条正式主线，不再存在 `pairwise`、双路径或仲裁阶段
- Prompt、Schema 与 Evals 围绕同一套双输入 `rubric` 版本同步演进
- 对外正式结果结构保持稳定，不因内部架构调整而频繁变更
