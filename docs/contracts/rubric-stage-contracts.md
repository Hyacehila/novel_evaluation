# 面向网络小说双输入全 LLM Rubric 阶段契约

## 适用主线

正式评分主线固定为：

1. `input_screening`
2. `rubric_evaluation`
3. `consistency_check`
4. `aggregation`
5. `final_projection`

## 共享枚举

### `stage`

- `input_screening`
- `rubric_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

### `inputComposition`

- `chapters_outline`
- `chapters_only`
- `outline_only`

### `evaluationMode`

- `full`
- `degraded`

## 正式词表

### `axisId`

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

### `skeletonDimensionId`

- `marketAttraction`
- `narrativeExecution`
- `characterMomentum`
- `noveltyUtility`

## `InputScreeningResult`

关键字段：

- `chaptersSufficiency`
- `outlineSufficiency`
- `evaluationMode`
- `rateable`
- `continueAllowed`
- `segmentationPlan`

### `segmentationPlan`

`segmentationPlan` 正式冻结为结构化对象，字段固定为：

- `strategy`
- `segments[]`
- `overflowPolicy`
- `truncated`

约束：

- 只描述长文本切分边界
- 不得扩展为第二套评分路由

## `RubricEvaluationSet`

约束：

- `items` 必须覆盖全部 `8` 轴
- `degraded` 模式仍要输出全部 `8` 轴，只能通过置信度、风险或阻断信号表达受限

## `ConsistencyCheckResult`

约束：

- 只负责整理与冲突识别
- `continueAllowed=false` 时进入业务阻断，而不是伪低分结果

## `AggregatedRubricResult`

作用：

- 将 `8` 轴结果映射到旧四维骨架层
- 形成正式结果草案

## `FinalEvaluationProjection`

作用：

- 作为对外 `EvaluationResult` 前的最后内部投影层

约束：

- 不新增额外执行追踪字段
- 执行追踪统一进入 `EvalRecord` 与日志
- `blocked` 或 `not_available` 场景不创建伪 projection

## 文件归属

- 阶段对象继续统一落在 `packages/schemas/stages/`
- 不再保留阶段对象目录拆分待确认项
