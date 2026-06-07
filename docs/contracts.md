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
- `completed + not_available` 用于任务已结束但当前没有可展示结果的状态，例如执行中断后的恢复标记。

## 输入与分析模式

`POST /api/tasks` 的输入必须包含显式 `analysisMode`：

| analysisMode | 所需输入 | 禁止输入 | 说明 |
| --- | --- | --- | --- |
| `long_opening_outline` | `chapters` 和 `outline` | 无 | 长篇开篇正文 + 大纲评估 |
| `completed_fulltext` | `chapters` | `outline` | 已完成全文评估 |

校验规则：

- `long_opening_outline` 缺正文返回 `422`。
- `long_opening_outline` 缺大纲返回 `422`。
- `completed_fulltext` 缺正文返回 `422`。
- `completed_fulltext` 携带大纲返回 `422`。

`POST /api/provider-status/smoke-test` 是本机可访问的真实 provider auth smoke：

- 不创建任务，不写入结果库。
- provider 未配置返回 `409 PROVIDER_NOT_CONFIGURED`。
- 真实 provider 调用失败返回 `502/503/504`，错误码使用 `PROVIDER_FAILURE`、`DEPENDENCY_UNAVAILABLE`、`TIMEOUT` 或 `CONTRACT_INVALID`。
- 成功返回 `providerId`、`modelId`、`configurationSource`、`ok=true`、`durationMs`，不返回模型正文或 API key。

这些规则在 API schema 层阻断，不进入主链。系统不再根据材料缺口选择替代评分模式或替代 Prompt。

## 正式结果结构

公开结果只认 `EvaluationResultResource`：

- `resultStatus = available` 时，必须携带 `result + resultTime`
- `resultStatus = blocked/not_available` 时，不允许返回伪结果，必须只给 `message`

`EvaluationResult` 的公开主体固定为：

- `overall`
- `axes`
- `optional typeAssessment`

这就是当前前端展示、历史读取和 evals 工件共同使用的唯一正式结果形状。

## 当前阶段契约

### `input_screening`

固定输出：

- 输入组成 `inputComposition`
- 显式分析模式 `analysisMode`
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
- 每轴 `scoreBand / reason / evidenceRefs / confidence / riskTags`
- `axisSummaries`
- `missingRequiredAxes`
- `overallConfidence`

Prompt 与 schema 只接受现行 8 轴契约，不维护替代字段别名。

### `type_lens_evaluation`

固定输出：

- 与 `novelType` 对应的固定 `4` 个 lens
- 每个 lens 的 `scoreBand / reason / evidenceRefs / confidence`

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

聚合阶段只接受以上字段，不维护替代聚合别名。

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

## 持久化数据

- 历史任务条目仍按当前任务 schema 读取；结果只接受当前 `EvaluationResult` 结构。
- 损坏 JSON 或不满足当前结果结构的 payload 会在读取期被 schema 校验拒绝。
- 本地开发数据可通过停止 API 后删除 `var/novel-evaluation.sqlite3` 重建。
- 持久化规则由 `packages/runtime/persistence.py` 负责，不在 API 或前端保留第二套转换逻辑。
