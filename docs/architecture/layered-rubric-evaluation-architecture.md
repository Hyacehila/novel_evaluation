# 面向网络小说的双输入分阶段 Rubric 评分架构

## 文档目标

本文档描述当前代码中的正式评分主线。现状以 `packages/application/scoring_pipeline/*` 与 `packages/schemas/*` 为准，而不是以早期设计稿中的旧四维顶层结果结构为准。

当前实现的核心结论是：

- 评分仍采用单主线分阶段编排
- 主评价层是 `8` 个 rubric 轴
- 对外正式结果是 `overall + axes`
- 旧四维骨架不再作为正式阶段输出或 API 结果字段

## 适用输入

正式输入仍是联合投稿包：

- `chapters + outline`：推荐输入
- `chapters only`：允许，进入降级评测
- `outline only`：允许，进入降级评测

说明：

- 输入组成由 `input_screening` 决定为 `chapters_outline / chapters_only / outline_only`
- 只有单侧输入时，`evaluationMode=degraded`
- 降级语义会体现在 rubric 结果和最终分数上

## 当前正式结果结构

`EvaluationResult` 当前固定为：

- `taskId`
- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `resultTime`
- `axes`
- `overall`

### `axes`

固定覆盖全部 `8` 个 rubric 轴，每个轴包含：

- `axisId`
- `scoreBand`
- `score`
- `summary`
- `reason`
- `degradedByInput`
- `riskTags`

### `overall`

包含：

- `score`
- `verdict`
- `summary`
- `platformCandidates`
- `marketFit`

说明：

- 旧版顶层字段 `signingProbability / commercialValue / writingQuality / innovationScore / detailedAnalysis` 已不再属于当前正式结果
- 对外 API 与前端页面都围绕 `overall + axes` 消费

## 当前 `8` 轴

| 轴 ID | 当前关注点 |
| --- | --- |
| `hookRetention` | 开局留存与继续阅读动力 |
| `serialMomentum` | 连载推进惯性与后续承接能力 |
| `characterDrive` | 主角驱动、关系张力与行动动力 |
| `narrativeControl` | 叙事组织、信息投放与语言控制 |
| `pacingPayoff` | 节奏铺垫与兑现关系 |
| `settingDifferentiation` | 设定差异化与卖点利用度 |
| `platformFit` | 内容调性与目标平台匹配度 |
| `commercialPotential` | 连载商业表现潜力 |

## 当前评分主线

```text
input_screening
-> rubric_evaluation
-> consistency_check
-> aggregation
-> final_projection
```

### 1. `input_screening`

职责：

- 判断输入是否可评
- 判断 `chapters` 与 `outline` 是否足量
- 输出 `inputComposition` 与 `evaluationMode`
- 对不可评输入给出阻断语义

阻断后果：

- `continueAllowed=false` 时直接以结构化错误结束，不继续后续阶段

### 2. `rubric_evaluation`

职责：

- 对 `8` 轴进行结构化 pointwise 评价
- 为每个轴提供理由、证据、风险标签与置信度
- 输出轴级摘要与总体置信度

当前执行方式：

- 实际上分 `3` 个 slice 调用 provider，再合并为完整结果
- slice 计划固定为：
  - `[hookRetention, serialMomentum, characterDrive]`
  - `[narrativeControl, pacingPayoff, settingDifferentiation]`
  - `[platformFit, commercialPotential]`

每个 rubric item 当前包含：

- `evaluationId`
- `axisId`
- `scoreBand`
- `reason`
- `evidenceRefs`
- `confidence`
- `riskTags`
- `blockingSignals`
- `affectedSkeletonDimensions`
- `degradedByInput`

说明：

- `affectedSkeletonDimensions` 仍存在，但只是 rubric 项上的兼容映射元数据
- 当前没有正式的“旧四维骨架阶段输出对象”

### 3. `consistency_check`

职责：

- 检查跨输入冲突
- 检查无依据结论
- 检查重复处罚
- 检查缺失必需轴
- 记录归一化说明

当前冲突类型包括：

- `cross_input_mismatch`
- `unsupported_claim`
- `duplicated_penalty`
- `missing_required_axis`
- `weak_evidence`

阻断后果：

- `continueAllowed=false` 时，流程以 `blocked` 语义结束

### 4. `aggregation`

职责：

- 读取 screening、rubric、consistency 三阶段结果
- 生成总体结论草案
- 输出平台候选与市场判断草案
- 汇总风险标签与总体置信度

当前正式输出字段为：

- `overallVerdictDraft`
- `overallSummaryDraft`
- `platformCandidates`
- `marketFitDraft`
- `riskTags`
- `overallConfidence`

说明：

- `aggregation` 当前不再输出旧四维骨架对象
- 也不再输出对外四分字段草案

### 5. `final_projection`

职责：

- 把 rubric 轴结果与 aggregation 草案投影成正式 `EvaluationResult`
- 将 `scoreBand` 映射为轴分数
- 计算 `overall.score`

当前分值映射为：

| `scoreBand` | 轴分数 |
| --- | --- |
| `0` | `20` |
| `1` | `35` |
| `2` | `55` |
| `3` | `75` |
| `4` | `90` |

当前总体分数计算规则：

- 先取 `8` 轴分数平均值
- `degraded` 模式减 `8`
- 若一致性阶段检测到重复处罚，减 `3`
- 若存在 `weak_evidence` 冲突，减 `4`
- 最终结果夹紧在 `0-100`

## 风险与降级语义

### 风险标签

当前风险标签来自 `FatalRisk` 枚举，例如：

- `aiManualTone`
- `staleFormula`
- `conceptSpam`
- `fakePayoff`
- `nonNarrativeSubmission`
- `insufficientMaterial`

风险标签可出现在：

- rubric item 的 `riskTags`
- aggregation 的 `riskTags`
- final result 每个 axis 的 `riskTags`

### 降级语义

- 单侧输入允许进入评分流程
- rubric item 会通过 `degradedByInput=true` 标记受输入不足影响的轴
- 最终总体分数会额外施加降级扣分

## 与旧结构的关系

当前代码中仍保留两类旧结构痕迹：

- `SkeletonDimensionId`：用于 rubric item 的 `affectedSkeletonDimensions` 兼容映射
- 个别归一化逻辑会识别旧 provider 输出别名

但需要明确：

- 这些痕迹不代表当前正式输出仍是旧四维骨架
- 当前 API、前端、结果 schema 的唯一正式结果形态是 `overall + axes`

## Prompt 与 Schema 落点

- `input_screening`、`rubric_evaluation`、`aggregation` 都通过 prompt runtime 解析
- 正式对外结果落在 `packages/schemas/output/result.py`
- 中间阶段契约落在 `packages/schemas/stages/*.py`
- 编排逻辑落在 `packages/application/scoring_pipeline/*`

## 当前成功标准

- 流程能稳定处理双输入与单侧降级输入
- rubric 阶段完整覆盖全部 `8` 轴
- 一致性阶段能阻断明显冲突或无依据结论
- 对外结果稳定保持 `overall + axes`
- 前后端围绕同一结果结构消费，不再回映射到旧四项评分
