# 面向网络小说的 V2 类型化 Rubric 评分架构

## 文档目标

本文档描述当前代码中的正式评分架构。现状以 `packages/application/scoring_pipeline/*`、`packages/schemas/*` 与当前前端结果页为准。

当前实现的核心结论是：

- 评分仍采用单主线分阶段编排
- 主评价层仍是通用 `8` 轴 rubric
- 在主评价层之外，新增一条解耦的“类型判断 -> 类型 lens”主线
- 对外正式结果是 `overall + axes + optional typeAssessment`
- 旧四维骨架不再作为正式阶段输出或 API 结果字段

## 适用输入

正式输入仍是联合投稿包：

- `chapters + outline`：推荐输入
- `chapters only`：允许，进入降级评测
- `outline only`：允许，进入降级评测

说明：

- 输入组成由 `input_screening` 决定为 `chapters_outline / chapters_only / outline_only`
- 只有单侧输入时，`evaluationMode=degraded`
- 降级语义会体现在通用 rubric、类型 lens 和最终分数上

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
- `typeAssessment`（可选）

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
- `verdictSubQuote`
- `summary`
- `platformCandidates`
- `marketFit`
- `strengths`
- `weaknesses`

### `typeAssessment`

当前保持可选，用于兼容历史结果读取。新任务的正式成功结果应填充：

- `novelType`
- `classificationConfidence`
- `fallbackUsed`
- `summary`
- `lenses`

每个 lens 包含：

- `lensId`
- `label`
- `scoreBand`
- `reason`
- `confidence`
- `degradedByInput`
- `riskTags`

## 当前通用 `8` 轴

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

## 当前类型体系

V2 固定使用以下 `8` 类：

| `NovelType` | 页面标签 | 当前固定 lens |
| --- | --- | --- |
| `female_general` | 女频通用 | 情绪钩子与代入 / 关系张力与人物吸引 / 情绪递进与兑现 / 圈层承诺与陪伴价值 |
| `fantasy_upgrade` | 玄幻升级 | 升级回路清晰度 / 力量体系可读性 / 奖励密度 / 奇观爽点兑现 |
| `urban_reality` | 都市现实 | 现实抓手 / 地位跃迁经营张力 / 行业现实可信度 / 连载转化抓手 |
| `history_military` | 历史军事 | 权力战争格局清晰度 / 历史质感可信度 / 谋略兑现 / 长线争霸推进 |
| `sci_fi_apocalypse` | 科幻末世 | 概念可利用度 / 规则闭环 / 生存技术压力系统 / 世界扩展潜力 |
| `suspense_horror` | 悬疑惊悚 | 谜面钩子 / 线索公平性 / 紧张维持 / 揭示兑现 |
| `game_derivative` | 游戏衍生 | 副本循环清晰度 / 规则反馈明确性 / build玩法变化 / 长线 escalations |
| `general_fallback` | 通用兜底 | premise 与钩子 / 核心冲突与目标 / 执行与可读性 / 连载潜力 |

实现约束：

- `female_general` 是单一女频 lens，不再细分子类型
- 男频当前覆盖 `6` 个窄类型 + `general_fallback`
- 低置信或类别接近时统一回落到 `general_fallback`

## 当前评分主线

```text
input_screening
-> type_classification
-> rubric_evaluation
-> type_lens_evaluation
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

### 2. `type_classification`

职责：

- 独立调用 provider 输出 `Top-3` 候选类型
- 生成结构化分类理由
- 依据固定阈值选择最终 `novelType`

当前选型规则：

- 若 `top1.confidence >= 0.60` 且 `top1 - top2 >= 0.12`，采用 `top1`
- 否则强制采用 `general_fallback`
- fallback 不阻断任务，只改变后续 lens 路径

### 3. `rubric_evaluation`

职责：

- 对 `8` 轴进行结构化 pointwise 评价
- 为每个轴提供理由、证据、风险标签与置信度
- 输出轴级摘要与总体置信度

当前执行方式：

- 分 `3` 个 slice 调用 provider，再合并为完整结果

### 4. `type_lens_evaluation`

职责：

- 独立调用 provider，只对最终类型的 `4` 个 lens 打分
- 输出类型 summary 与 `4` 个 lens item

当前实现方式：

- prompt runtime 只区分 `default / degraded`
- 各类型差异由后端维护的 lens 目录注入 user payload

### 5. `consistency_check`

职责：

- 检查跨输入冲突
- 检查无依据结论
- 检查重复处罚
- 检查缺失必需轴
- 记录归一化说明

### 6. `aggregation`

职责：

- 同时读取 screening、type classification、rubric、type lens、consistency
- 输出总体结论草案、平台候选、市场判断与优势劣势草案
- 在结论文案中显式体现“作品属于什么类型、按什么 lens 评、为什么这样评”

### 7. `final_projection`

职责：

- 把 rubric 轴结果、类型结果和 aggregation 草案投影成正式结果
- 计算 `overall.score`
- 生成 `typeAssessment`

## 当前总体分数公式

`packages/application/scoring_pipeline/projection_service.py` 当前逻辑：

- `universalBase = 8` 轴分数平均值
- `lensBase = 4` 个类型 lens 分数平均值
- `typeWeight = 0.25`
- 若 `novelType == general_fallback`，`typeWeight = 0.15`
- `combinedBase = round(universalBase * (1 - typeWeight) + lensBase * typeWeight)`
- 在 `combinedBase` 上继续施加：
  - `degraded` 减 `8`
  - `duplicated_penalty` 减 `3`
  - `weak_evidence` 减 `4`
- 最终夹紧到 `0-100`

## 任务页与结果页的外显方式

### 任务详情页

- 固定存在“类型识别”区域
- 若 `novelType` 尚未写回，显示“识别中”
- 若已写回，显示：
  - 类型 badge
  - 识别置信度
  - 是否触发兜底

### 结果详情页

- 总体判断模块保持不变
- 在总体判断与 `8` 轴之间新增独立“类型评价模块”
- 若 `typeAssessment` 缺失，则隐藏该模块，不影响历史结果阅读

## 与旧结构的关系

当前代码中仍保留两类旧结构痕迹：

- `SkeletonDimensionId`：用于 rubric item 的兼容映射元数据
- 个别归一化逻辑会识别旧 provider 输出别名

但需要明确：

- 这些痕迹不代表当前正式输出仍是旧四维骨架
- 当前 API、前端、结果 schema 的唯一正式结果形态是 `overall + axes + optional typeAssessment`
