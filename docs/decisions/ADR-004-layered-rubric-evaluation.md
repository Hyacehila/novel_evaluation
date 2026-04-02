# ADR-004：采用面向网络小说的双输入全 LLM 分阶段 Rubric 评分架构作为正式主线

> 历史说明：本文记录的是当时接受的架构决策背景。当前代码实现已进一步收敛，正式对外结果为 `overall + axes + optional typeAssessment`，并新增解耦的 `type_classification / type_lens_evaluation` 主线。旧四维骨架不再作为正式 `aggregation` 输出，对外四分字段也已移除。现状请以 `docs/architecture/layered-rubric-evaluation-architecture.md`、`docs/architecture/scoring-pipeline.md` 与 `docs/contracts/json-contracts.md` 为准。

## 状态

已接受。

## 背景

当前仓库已经明确以下长期约束：

- 系统核心能力是 `LLM as Judge`
- 正式评分主线采用全 `LLM` 分阶段 `rubric` 机制
- Prompt 只允许在后端治理
- 正式输出必须是严格 JSON
- `packages/schemas/` 是正式结构契约的唯一真源
- 当前仓库仍处于结构、契约与治理优先阶段

在此前主线冻结的基础上，当前产品方向进一步明确为：系统不再泛化服务任意小说片段评分，而是优先服务网络小说投稿评估场景，正式输入以“已写章节正文 + 后续大纲规划”的联合材料为中心。

这意味着正式评分架构需要同时回答三个问题：

- 如何把章节正文与后续大纲放进同一条正式主线中进行联合判断
- 如何把面向网文连载判断的新 `8` 轴评价层，与既有对外四分字段稳定衔接
- 如何在不引入额外分叉评分路径的前提下，让评分既可解释、又可被后续开发直接消费

## 决策选项

### 方案 A：继续以单文本整体直评为主

优点：

- 实现最简单
- 调用链最短
- 早期最容易快速出结果

缺点：

- 无法稳定处理“章节正文 + 后续大纲”的联合判断
- 难以拆分正文表现与大纲承诺之间的一致性问题
- 评分理由难以沉淀为可回归资产
- 会重新回到黑盒整体判断

### 方案 B：保留旧四维作为唯一内部主评价层

优点：

- 与现有对外字段关系较近
- 文档改动面较小
- 迁移成本较低

缺点：

- 对网文连载语境下的判断表达力不足
- 难以显式承载 `platformFit`、连载动能、兑现能力等关键判断
- 会把多个不同问题重新挤压回宽泛维度中，降低后续 Prompt 与 Evals 的可治理性

### 方案 C：采用双输入 + 新 8 轴主评价层 + 旧四维骨架层 + 最终四分投影

优点：

- 能直接服务网络小说投稿评估场景
- 能把正文表现、大纲承诺和跨输入一致性纳入同一主线
- 能以更贴近编辑判断的 `8` 轴承载网文评价逻辑
- 继续保留旧四维作为中间骨架层，避免对外字段语义漂移
- 更适合围绕 Prompt、Schema 与 Evals 做版本治理

缺点：

- 文档、契约与映射关系会更复杂
- 多阶段模型调用成本更高
- 若契约设计不清晰，聚合层仍可能黑盒化

### 方案 D：引入 `pairwise` 或额外分叉评分路径

优点：

- 理论上可用于处理边界样本比较
- 理论上可以引入额外仲裁手段

缺点：

- 与当前需求冲突
- 会破坏单主线治理边界
- 会显著增加 Prompt、Schema 与 Evals 的治理负担
- 会让正式开发边界重新变得模糊

## 决策

采用 **方案 C：双输入 + 新 `8` 轴主评价层 + 旧四维骨架层 + 最终四分投影** 作为正式评分主线的内部结构。

正式主线仍固定为五段：

1. `输入预检查`
2. `LLM rubric 分点评价`
3. `轻量一致性整理`
4. `新模型聚合输出`
5. `正式结果投影`

在这条主线中，正式评分对象固定为联合输入：

- `chapters`：作者上传的前几章节正文
- `outline`：作者上传的后续大纲规划

系统必须把这两类材料视为同一投稿包中的两个组成部分，而不是两个互相独立的评分任务。

## 具体原则

### 1. 正式输入采用双输入联合模型

正式投稿对象至少支持以下组合：

- `chapters + outline`
- `chapters only`
- `outline only`

其中：

- `chapters + outline` 是正式推荐输入形态
- `chapters only` 与 `outline only` 可以进入降级评估
- 是否降级、置信度是否下降、哪些轴可稳定判断，都必须通过结构化契约显式表达

### 2. 正式评分只保留 `pointwise`

系统正式评分主线只保留 `pointwise` 分点评价：

- 不引入 `pairwise`
- 不引入额外比较式支路
- 不通过隐式多候选比较来决定正式结果
- 使用 Prompt 约束、封闭词表与通用 examples 控制判断风格与尺度

### 3. 新 `8` 轴作为主评价层

正式 `rubric` 主评价层固定为以下 `8` 轴：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

这 `8` 轴用于承载网络小说连载判断中的主要评价职责。

### 4. 旧四维保留为中间骨架层

既有四个中间骨架维度继续保留，但不再作为最上层主评价层：

- `marketAttraction`
- `narrativeExecution`
- `characterMomentum`
- `noveltyUtility`

它们承担两类职责：

- 把新 `8` 轴映射为更稳定的内部汇总层
- 继续承接对外正式四分字段的来源关系

### 5. `platformFit` 升级为独立顶层评价轴

平台适配性不再只是市场吸引力的从属子项，而是独立顶层轴。

原因：

- 网文投稿场景下，平台适配会显著影响签约判断
- 同样的内容在不同平台读者预期下商业表现可能完全不同
- 该能力需要被明确评测、校准与追踪，不适合继续隐含在宽泛维度里

### 6. `fatalRisk` 作为跨层约束维度保留

`fatalRisk` 不属于新 `8` 轴之一，也不属于普通加权分项，而是跨层约束维度。

它用于处理以下问题：

- `aiManualTone`
- `staleFormula`
- `conceptSpam`
- `fakePayoff`
- `nonNarrativeSubmission`
- `insufficientMaterial`

其作用方式是：

- 对 `8` 轴评价给出约束信号
- 对旧四维骨架层给出上限或惩罚信号
- 对最终四分字段给出压制、封顶或不可评结论

### 7. 对外结构稳定，内部判断分层

对外继续保留稳定正式结果字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

内部则采用三层映射：

1. 新 `8` 轴主评价层
2. 旧四维骨架层
3. 对外四分投影层

### 8. 一致性整理聚焦跨输入冲突

轻量一致性整理继续保留，但重点从一般缺项检查扩展到跨输入冲突检查，例如：

- 正文章节承载出的卖点，与大纲承诺明显不一致
- 大纲宣称后续有强兑现，但前文没有足够铺垫
- 大纲极度依赖设定补偿，但正文没有体现承接能力

一致性阶段只负责发现和整理问题，不承担分叉升级或仲裁职责。

## 结构映射原则

### 新 `8` 轴 → 旧四维骨架层

- `hookRetention`、`serialMomentum`、`platformFit`、`commercialPotential` 主要映射到 `marketAttraction`
- `narrativeControl`、`pacingPayoff` 主要映射到 `narrativeExecution`
- `characterDrive` 主要映射到 `characterMomentum`
- `settingDifferentiation` 主要映射到 `noveltyUtility`

说明：

- 映射允许一轴影响多个骨架维度
- 但每一轴必须存在明确主归属，避免聚合规则失真

### 旧四维骨架层 → 对外四分字段

- `marketAttraction` 主要影响 `commercialValue`
- `narrativeExecution` 主要影响 `writingQuality`
- `characterMomentum` 同时影响 `commercialValue` 与 `writingQuality`
- `noveltyUtility` 主要影响 `innovationScore`
- `signingProbability` 建立在前三项基础分之上，并受 `platformFit` 与 `fatalRisk` 强约束

## 非目标

以下内容不进入当前正式主线：

- `pairwise` 评分
- 外部人工仲裁型正式入口
- 并行评分路径
- 额外升级链路
- 前端直接拼接或持有正式 Prompt
- 把研究产物目录中的临时结论当作正式规则真源

## 预期结果

若该提案被接受，系统将形成以下长期收益：

- 正式评分对象从单文本扩展为面向投稿包的联合输入
- 新 `8` 轴能更准确表达网络小说评估逻辑
- 旧四维与对外四分字段继续保持稳定衔接
- Prompt、Schema、Evals 与后续 API 文档可以围绕同一主线同步演进
- 正文表现、大纲承诺与跨输入一致性可以被统一治理

同时，也会引入以下治理成本：

- 契约层需要同时维护输入组成、跨输入证据与降级语义
- 聚合层需要解释新 `8` 轴与旧四维之间的映射关系
- `evals/` 需要新增联合输入样本与跨输入冲突样本

## 后续动作

- 先重写 `docs/architecture/layered-rubric-evaluation-architecture.md`
- 再重写 `docs/planning/rubric-design-absorption-matrix.md`
- 再重写 `docs/contracts/rubric-stage-contracts.md`
- 然后同步 `docs/contracts/json-contracts.md` 与 `docs/architecture/scoring-pipeline.md`
- 最后同步 API、前端、Prompt、Evals 与 Phase 1 范围文档
