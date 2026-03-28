# 评分流水线

本文档定义小说智能打分系统的正式评分流程。

当前仓库只保留一条正式主线：

- **正式评分流程**：输入预检查 → `8` 轴 `LLM rubric` 分点评价 → 轻量一致性整理 → 聚合草案输出 → 正式结果投影

相关专题文档：

- `docs/contracts/rubric-stage-contracts.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/architecture/provider-abstraction.md`

## 正式评分流程

1. 接收用户提交的联合输入
2. 校验输入结构与基本边界
3. 创建 `EvaluationTask`
4. 通过 Prompt runtime 解析阶段绑定
5. 执行 `input_screening`
6. 执行 `rubric_evaluation`
7. 执行 `consistency_check`
8. 执行 `aggregation`
9. 执行 `final_projection`
10. 生成正式 `EvaluationResult`
11. 持久化任务、结果和日志

## 技术承接关系

- `apps/api` 负责接口边界、后台执行和结果读取
- `packages/application.services.EvaluationService` 负责任务创建、状态推进和主流程入口
- `packages/application.scoring_pipeline` 负责各阶段编排
- `packages/provider-adapters` 负责把真实模型调用收敛到统一 `execute()` 接口
- `packages/schemas/` 是正式结构真源

## 各阶段职责

### 1. `input_screening`

- 判断输入组成是 `chapters_outline / chapters_only / outline_only`
- 判定 `evaluationMode` 是 `full` 还是 `degraded`
- 给出 `chaptersSufficiency / outlineSufficiency`
- 决定是否 `continueAllowed`
- 绑定本次任务使用的 `schemaVersion / promptVersion / rubricVersion / providerId / modelId`

### 2. `rubric_evaluation`

- 输出完整 `8` 轴的 `RubricEvaluationSet`
- 每个评价项都包含 `scoreBand / reason / evidenceRefs / riskTags / degradedByInput`
- 当前实现不会一次请求全部 `8` 轴，而是按以下切片执行后再合并：
  - `hookRetention / serialMomentum / characterDrive`
  - `narrativeControl / pacingPayoff / settingDifferentiation`
  - `platformFit / commercialPotential`
- 每个切片先验证为 `RubricEvaluationSlice`，再合并为完整 `RubricEvaluationSet`

### 3. `consistency_check`

- 当前为本地一致性整理逻辑，不额外调用 provider
- 检查：
  - `cross_input_mismatch`
  - `unsupported_claim`
  - `duplicated_penalty`
  - `missing_required_axis`
  - `weak_evidence`
- 若存在高严重度冲突，会直接阻断结果，不进入伪低分成功态

### 4. `aggregation`

- 再次调用 provider 生成聚合草案
- 当前正式输出字段是：
  - `overallVerdictDraft`
  - `overallSummaryDraft`
  - `platformCandidates`
  - `marketFitDraft`
  - `riskTags`
  - `overallConfidence`
- 当前实现不再把旧四维骨架作为正式 schema 输出

### 5. `final_projection`

- 直接把 rubric `8` 轴映射为结果页展示的 `axes`
- 把聚合草案映射为 `overall.verdict / overall.summary / overall.platformCandidates / overall.marketFit`
- `overall.score` 由 `8` 轴分值均值推导，并结合以下因素做轻量扣减：
  - `degraded` 模式
  - `duplicatedPenaltiesDetected`
  - `weak_evidence`

## Provider 执行约束

- provider 请求统一走 `execute_provider_stage()`
- 每个阶段请求都会带：
  - 阶段 Prompt 正文
  - JSON 序列化后的用户载荷
  - `timeoutMs / maxTokens / responseFormat`
- 上游 provider 失败会被收敛并清洗为统一错误语义，不把原始异常文本直接暴露给用户

## 结果与持久化

- `final_projection` 先生成 `FinalEvaluationProjection`
- `EvaluationService` 再将其转换为正式 `EvaluationResult`
- 结果资源以 `EvaluationResultResource` 形式持久化
- 若持久化结果是旧 schema 或损坏 payload，后续读取会降级为 `not_available`

## 设计目标

- 流水线标准化
- 阶段边界清晰
- 契约优先
- 错误语义稳定
- 本地部署可运行
