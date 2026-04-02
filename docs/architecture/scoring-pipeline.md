# 评分流水线

本文档定义当前代码中的正式评分流程。现状以 `packages/application/scoring_pipeline/*`、`packages/application/services/evaluation_service.py` 与 `packages/schemas/*` 为准。

## 当前正式主线

```text
input_screening
-> type_classification
-> rubric_evaluation
-> type_lens_evaluation
-> consistency_check
-> aggregation
-> final_projection
```

说明：

- `type_classification` 和 `type_lens_evaluation` 都是独立的 LLM 请求
- `consistency_check` 与 `final_projection` 是本地逻辑，不额外调用 provider
- `rubric_evaluation` 仍是正式评分主轴，类型 lens 只作为并行补充维度
- `aggregation` 同时读取 screening、类型、通用 rubric、类型 lens 和一致性结果

## 技术承接关系

- `apps/api` 负责接口边界、后台执行和结果读取
- `packages/application.services.EvaluationService` 负责任务创建、状态推进和主流程入口
- `packages/application.scoring_pipeline` 负责阶段编排与结果投影
- `packages/provider-adapters` 负责把真实模型调用收敛到统一 `execute()` 接口
- `packages/schemas/` 是正式结构真源

## 正式阶段职责

### 1. `input_screening`

- 判断输入组成是 `chapters_outline / chapters_only / outline_only`
- 判定 `evaluationMode` 是 `full` 还是 `degraded`
- 给出 `chaptersSufficiency / outlineSufficiency`
- 决定是否 `continueAllowed`
- 绑定本次任务使用的 `schemaVersion / promptVersion / rubricVersion / providerId / modelId`

阻断语义：

- `continueAllowed=false` 时，流程直接以结构化错误结束
- `EvaluationService` 会将任务结束为 `completed + blocked`

### 2. `type_classification`

- 独立调用 provider，输出固定 `Top-3` 候选类型
- 当前正式类型枚举为：
  - `female_general`
  - `fantasy_upgrade`
  - `urban_reality`
  - `history_military`
  - `sci_fi_apocalypse`
  - `suspense_horror`
  - `game_derivative`
  - `general_fallback`
- 后端按固定规则选最终类型：
  - `top1.confidence >= 0.60`
  - 且 `top1 - top2 >= 0.12`
  - 否则强制回落到 `general_fallback`
- `female_general` 不再细分女频子类型

任务元数据同步：

- `EvaluationService` 会在该阶段完成后立即把 `novelType / typeClassificationConfidence / typeFallbackUsed` 写回任务
- 因此前端任务页在任务尚未结束时就可能显示类型识别结果

### 3. `rubric_evaluation`

- 输出完整 `8` 轴的 `RubricEvaluationSet`
- 每个评价项都包含 `scoreBand / reason / evidenceRefs / confidence / riskTags / degradedByInput`
- 当前实现不会一次请求全部 `8` 轴，而是按以下切片执行后再合并：
  - `hookRetention / serialMomentum / characterDrive`
  - `narrativeControl / pacingPayoff / settingDifferentiation`
  - `platformFit / commercialPotential`

### 4. `type_lens_evaluation`

- 独立调用 provider，只评当前最终类型对应的 `4` 个 lens
- 每个 lens 固定输出：
  - `lensId`
  - `label`
  - `scoreBand`
  - `reason`
  - `evidenceRefs`
  - `confidence`
  - `riskTags`
  - `degradedByInput`
- 类型差异不通过复制多套 prompt runtime selector 实现
- 当前实现由后端维护固定类型 lens 目录，并在 user payload 中注入给模型

### 5. `consistency_check`

- 当前为本地一致性整理逻辑，不额外调用 provider
- 检查：
  - `cross_input_mismatch`
  - `unsupported_claim`
  - `duplicated_penalty`
  - `missing_required_axis`
  - `weak_evidence`
- 若存在高严重度冲突，会直接阻断结果，不进入伪低分成功态

### 6. `aggregation`

- 再次调用 provider 生成聚合草案
- 当前正式输入来自：
  - `screening`
  - `type_classification`
  - `rubric`
  - `type_lens`
  - `consistency`
- 当前正式输出字段是：
  - `overallVerdictDraft`
  - `verdictSubQuote`
  - `overallSummaryDraft`
  - `platformCandidates`
  - `marketFitDraft`
  - `strengthCandidates`
  - `weaknessCandidates`
  - `riskTags`
  - `overallConfidence`

### 7. `final_projection`

- 直接把 rubric `8` 轴映射为结果页展示的 `axes`
- 把聚合草案映射为 `overall`
- 把类型判断与类型 lens 映射为可选 `typeAssessment`
- 生成正式 `FinalEvaluationProjection`，再由 `EvaluationService` 持久化为 `EvaluationResult`

## 总分计算规则

`packages/application/scoring_pipeline/projection_service.py` 当前按以下公式计算 `overall.score`：

1. `universalBase = 8` 轴分数平均值
2. `lensBase = 4` 个类型 lens 分数平均值
3. `typeWeight = 0.25`
4. 若 `novelType == general_fallback`，`typeWeight = 0.15`
5. `combinedBase = round(universalBase * (1 - typeWeight) + lensBase * typeWeight)`
6. 在 `combinedBase` 上继续施加罚分：
   - `degraded` 减 `8`
   - `duplicated_penalty` 减 `3`
   - `weak_evidence` 减 `4`
7. 最终夹紧到 `0-100`

当前 `scoreBand -> 轴分数` 映射为：

| `scoreBand` | 分值 |
| --- | --- |
| `0` | `20` |
| `1` | `35` |
| `2` | `55` |
| `3` | `75` |
| `4` | `90` |

## 结果与持久化

- `FinalEvaluationProjection` 当前正式结构为 `overall + axes + optional typeAssessment`
- `EvaluationResult` 与 `EvaluationResultResource` 位于 `packages/schemas/output/result.py`
- `typeAssessment` 当前保持可选，以兼容历史结果读取
- 新任务的正式成功结果应填充 `typeAssessment`
- 若持久化结果是旧 schema 或损坏 payload，后续读取会降级为 `not_available`

## Provider 执行约束

- provider 请求统一走 `execute_provider_stage()`
- 每个 provider stage 请求都会带：
  - 阶段 Prompt 正文
  - JSON 序列化后的用户载荷
  - `timeoutMs / maxTokens / responseFormat`
- 上游 provider 失败会被收敛并清洗为统一错误语义，不把原始异常文本直接暴露给用户
