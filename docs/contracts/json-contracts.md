# JSON 契约说明

本文档定义系统必须遵守的结构化输出原则。

## 总原则

- 模型输出必须是严格 JSON
- API 返回必须符合正式 Schema
- 不允许在 JSON 外附带多余自然语言
- 不允许返回缺失核心字段的半结构化结果

## 当前确认的核心输出字段

顶层评分字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

列表与对象字段：

- `strengths`
- `weaknesses`
- `sortingHat.platforms`
- `marketFit`
- `editorVerdict`
- `detailedAnalysis.plot`
- `detailedAnalysis.character`
- `detailedAnalysis.pacing`
- `detailedAnalysis.worldBuilding`

## 结构要求

- 顶层评分应为 `0-100` 的整数
- 平台推荐应为数组
- 平台项应包含 `name`、`percentage`、`reason`
- 详细分析应为对象并包含固定字段
- 强项与弱项应为字符串数组

## 治理原则

- 正式 Schema 应在 `packages/schemas/` 维护
- 文档只负责解释契约含义，不代替正式定义
- Prompt、Provider、API 输出都必须围绕同一契约协同
