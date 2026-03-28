# `packages/application`

## 模块角色

该模块承载应用用例编排与流程组织能力，是后端运行时把领域对象、Prompt、Provider、Schema 和执行入口串起来的主用例层。

## 输入对象

该模块当前主要消费：

- `JointSubmissionRequest`
- `Manuscript`
- `EvaluationTask`
- 阶段契约对象：
  - `InputScreeningResult`
  - `RubricEvaluationSlice`
  - `RubricEvaluationSet`
  - `ConsistencyCheckResult`
  - `AggregatedRubricResult`
  - `FinalEvaluationProjection`

## 输出对象

该模块当前主要产出：

- `EvaluationTask`
- `EvaluationTaskSummary`
- `EvaluationResultResource`
- `EvaluationResult`
- `DashboardSummary`
- `HistoryList`
- `ScoringPipelineResult`
- 面向 worker / API 的统一 use case 返回对象

## 主要职责

- 创建任务
- 读取任务
- 读取结果
- 读取 dashboard / history
- 组织正式评分主线
- 选择 Prompt / schema / provider 版本
- 统一任务状态推进与错误出口
- 在读取期把旧版或损坏结果标准化为 `not_available`

## 不负责

- 定义正式领域对象字段本体
- 定义正式 schema 真源
- 自行发明新的状态枚举
- 承载页面逻辑或前端 View Model
- 直接内嵌长期 Prompt 正文

## 依赖关系

该模块依赖：

- `packages/schemas/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `apps/api/contracts/` 中冻结的 API 资源语义

该模块被以下入口调用：

- `apps/api/`
- `apps/worker/`

## 错误语义

该模块必须沿用统一错误语义：

- 请求边界错误由 API 边界层拦截
- 业务阻断进入 `completed + blocked`
- 技术失败进入 `failed + not_available`
- 不允许在 use case 层伪造“低分但成功”的结果替代阻断
- provider 和 schema 失败都必须转为受控错误码

## Side Effects

该模块允许产生的 side effects：

- 创建与更新任务记录
- 记录执行元信息
- 调用 Prompt runtime
- 调用 Provider adapter
- 记录回归或审查所需的最小元信息

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "EvaluationTask|RubricEvaluationSet|ScoringPipelineResult|错误语义|验收方式" packages/application/README.md`

## DevFleet 使用约束

- 后续实现 mission 只能以本文档和上游契约文档为准
- 不得在实现阶段反向修改领域对象与状态真源
- 不得把一次 use case 任务扩写成多条评分主线
