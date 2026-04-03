# Contracts

## 代码真源

| 范围 | 真源 |
| --- | --- |
| 输入提交 | `packages/schemas/input/` |
| 内部阶段结果 | `packages/schemas/stages/` |
| 对外结果与状态 | `packages/schemas/output/` |
| 回归与批处理 | `packages/schemas/evals/` |
| 前端消费镜像 | `apps/web/src/api/contracts.ts` |

约束：

- `packages/schemas` 是正式字段真源。
- 本文档是解释真源，不是第二套定义。
- `apps/web/src/api/contracts.ts` 只保留前端当前实际消费的 DTO 镜像，不反向支配后端。

## API 资源

| 路由 | 语义 | 主返回对象 |
| --- | --- | --- |
| `GET /api/provider-status` | 读取 provider 状态 | `ProviderStatus` |
| `POST /api/provider-status/runtime-key` | 录入运行时 key | `ProviderStatus` |
| `DELETE /api/provider-status/runtime-key` | 仅 E2E/特定环境允许的重置 | `ProviderStatus` |
| `POST /api/tasks` | 创建任务 | `EvaluationTask` |
| `GET /api/tasks/{taskId}` | 读取任务详情 | `EvaluationTask` |
| `GET /api/tasks/{taskId}/result` | 读取结果资源 | `EvaluationResultResource` |
| `GET /api/dashboard` | 工作台摘要 | `DashboardSummary` |
| `GET /api/history` | 历史列表 | `HistoryList` |

所有 API 都返回统一 envelope：

- 成功：`{ success: true, data, meta? }`
- 失败：`{ success: false, error }`

## 任务状态语义

允许的 `(status, resultStatus)` 组合固定为：

- `queued + not_available`
- `processing + not_available`
- `completed + available`
- `completed + blocked`
- `completed + not_available`
- `failed + not_available`

解释：

- `blocked` 表示业务阻断，任务本身结束，但结果不满足正式展示条件。
- `failed` 表示技术失败。
- `completed + not_available` 主要用于读取期兼容降级，例如旧结果结构或损坏结果。

## 正式结果结构

公开结果只认 `EvaluationResultResource`：

- `resultStatus = available` 时，必须携带 `result + resultTime`
- `resultStatus = blocked/not_available` 时，不允许返回伪结果，必须只给 `message`

`EvaluationResult` 的公开主体固定为：

- `overall`
- `axes`
- `optional typeAssessment`

这就是当前前端展示和历史兼容的唯一正式结果形状。

## 当前阶段契约

### `input_screening`

固定输出：

- 输入组成 `inputComposition`
- 评分模式 `evaluationMode`
- 正文/大纲充分性
- `continueAllowed`
- 阻断原因与 `riskTags`

### `type_classification`

固定输出：

- Top-3 `candidates`
- 最终 `novelType`
- `classificationConfidence`
- `fallbackUsed`
- `summary`

### `rubric_evaluation`

固定输出：

- 全部 `8` 个轴
- 每轴 `scoreBand / reason / evidenceRefs / confidence / riskTags / degradedByInput`
- `axisSummaries`
- `missingRequiredAxes`
- `overallConfidence`

旧骨架字段已经移除，当前 Prompt 与 schema 只认现行 8 轴契约。

### `type_lens_evaluation`

固定输出：

- 与 `novelType` 对应的固定 `4` 个 lens
- 每个 lens 的 `scoreBand / reason / evidenceRefs / confidence / degradedByInput`

### `aggregation`

固定输出：

- `overallVerdictDraft`
- `verdictSubQuote`
- `overallSummaryDraft`
- `platformCandidates`
- `marketFitDraft`
- `strengthCandidates`
- `weaknessCandidates`
- `riskTags`
- `overallConfidence`

旧四分字段和旧编辑摘要字段不再属于现行契约。

### `final_projection`

职责只有一个：把 stage 结果投影成前端和历史可读的正式结果对象。

## Provider 与 Prompt 元数据

任务和结果都携带：

- `schemaVersion`
- `promptVersion`
- `rubricVersion`
- `providerId`
- `modelId`

这些字段由共享 runtime 与 prompt runtime 决定，不由前端生成。

## 历史兼容

- 旧持久化结果如果包含旧字段集合，会在读取期降级为 `not_available`。
- 损坏 JSON 同样降级为 `not_available`。
- 历史任务条目仍然可见；只是旧结果不再伪装成当前 8 轴结构。

这条兼容规则由 `packages/runtime/persistence.py` 负责，而不是通过保留旧 Prompt 或旧文档来维持。
