# JSON 契约说明

本文档定义系统必须遵守的结构化输出原则。

## 总原则

- 模型输出必须是严格 JSON
- API 返回必须符合正式 Schema 或正式 envelope 契约
- 不允许在 JSON 外附带多余自然语言
- 不允许返回缺失核心字段的半结构化结果

## 真源与运行时表达

- `packages/schemas/` 是正式结构契约的唯一真源
- `Pydantic` 负责 `apps/api` 边界 DTO 与运行时结构校验
- `Pydantic` 不替代 `packages/schemas/` 成为第二套正式定义
- 文档用于解释字段语义与治理规则，不替代正式 Schema 文件
- `PocketFlow` 阶段对象、Provider 适配结果与 API 返回对象都必须收敛到同一套结构语义

## 当前确认的核心输出字段

当前正式输出字段主要服务于对外 API 与结果消费层。

当前实现阶段：

- 这些字段由当前正式评分链路产出
- 当前文档不要求立即完成全部阶段化运行时实现

在目标态的全 `LLM` 分阶段 `rubric` 机制下：

- 对外字段仍保持稳定
- 对内允许存在更细粒度的阶段契约
- 内部 `rubric` 维度不要求与对外字段一一对应
- 对外字段应被视为内部 `rubric` 聚合后的正式投影

顶层评分字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

列表与对象字段：

- `strengths`
- `weaknesses`
- `platforms`
- `marketFit`
- `editorVerdict`
- `detailedAnalysis.plot`
- `detailedAnalysis.character`
- `detailedAnalysis.pacing`
- `detailedAnalysis.worldBuilding`

说明：

- 当前正式消费字段采用顶层 `platforms`
- 当前不使用 `sortingHat.platforms` 作为正式结果字段路径

## 字段与 Rubric 的关系

建议按以下原则理解正式字段与内部评分维度的关系：

- `commercialValue`：主要来自市场吸引力、连载潜力、平台适配度等内部维度
- `writingQuality`：主要来自叙事执行、语言控制、信息组织等内部维度
- `innovationScore`：主要来自新鲜度、设定有效性、题材差异化等内部维度
- `signingProbability`：应综合前三项基础分，并受风险维度、输入预检查结果与一致性整理结果约束
- `strengths` 与 `weaknesses`：应来自分点评价结果与聚合总结，而不是凭空生成
- `editorVerdict`、`marketFit` 与 `detailedAnalysis.*`：应视为聚合与投影层产物，而不是独立于评分过程的附属文案

说明：

- 当前文档只解释字段含义与映射方向
- 更细的阶段结构应在 `docs/contracts/rubric-stage-contracts.md` 与后续 `packages/schemas/` 中维护

## 结构要求

- 顶层评分应为 `0-100` 的整数
- `platforms` 应为顶层数组字段
- 平台项应包含 `name`、`percentage`、`reason`
- 详细分析应为对象并包含固定字段
- 强项与弱项应为字符串数组

## 治理原则

- 正式 Schema 应在 `packages/schemas/` 维护
- 文档只负责解释契约含义，不代替正式定义
- Prompt、Provider、API 输出都必须围绕同一契约协同
- 内部阶段契约与对外正式结果契约应分层治理
- Prompt 版本、Schema 版本、Provider 版本与评测基线应能关联追踪
