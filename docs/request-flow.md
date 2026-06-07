# Request Flow

本文描述一次 `POST /api/tasks` 从提交到结果落库的主链。系统只接受显式 `analysisMode`，不会根据输入缺口自动切换到其他 Prompt。

## Analysis Modes

| `analysisMode` | 输入要求 | 典型用途 |
| --- | --- | --- |
| `long_opening_outline` | 必须同时提交正文 `chapters` 和大纲 `outline` | 长篇开篇加后续规划评估 |
| `completed_fulltext` | 必须提交正文 `chapters`，且不得提交 `outline` | 已完成全文评估 |

无效组合在 API 入参阶段返回 `422`：

- `long_opening_outline` 缺正文。
- `long_opening_outline` 缺大纲。
- `completed_fulltext` 缺正文。
- `completed_fulltext` 携带大纲。

## Stage Order

| 顺序 | Stage | 调用 Provider | Prompt 路由 |
| --- | --- | --- | --- |
| 1 | `input_screening` | 是 | 按 `inputCompositionScope` + `analysisModeScope` + provider/model 选择正式 prompt |
| 2 | `type_classification` | 是 | 继承同一个 `analysisMode` |
| 3 | `rubric_evaluation` slice 1 | 是 | 评 3 个通用轴 |
| 4 | `rubric_evaluation` slice 2 | 是 | 再评 3 个通用轴 |
| 5 | `rubric_evaluation` slice 3 | 是 | 最后评 2 个通用轴 |
| 6 | `type_lens_evaluation` | 是 | 评最终类型对应的 4 个 lens |
| 7 | `consistency_check` | 否 | 本地一致性检查 |
| 8 | `aggregation` | 是 | 汇总总体判断草稿 |
| 9 | `final_projection` | 否 | 本地组装对外结果 |

Prompt registry 使用 `analysisModeScope` 区分两种正式输入模式。当前只应存在长篇开篇与全文两套正式 prompt；测试应断言 primary scopes 精确覆盖这两个路由。

## Execution Flow

1. API 先检查 provider 状态；没有启动期 key 或 runtime key 时，创建任务返回 `409 PROVIDER_NOT_CONFIGURED`，只读查询仍可用。
2. JSON 或 multipart 输入被解析成 `JointSubmissionRequest`，上传文件只支持 `TXT / MD / DOCX`，并受 `NOVEL_EVAL_UPLOAD_MAX_BYTES` 限制。
3. `EvaluationService` 创建 `queued + not_available` 任务，并由 API background task 推进执行。
4. 评分流水线按 stage 解析 Prompt、调用 provider、校验 stage schema；`consistency_check` 和 `final_projection` 是本地规则阶段。
5. 业务阻断写成 `completed + blocked`，技术失败写成 `failed + not_available`，成功结果写成 `completed + available`。
6. API、dashboard、history 和结果页都从同一个 SQLite repository 读取当前任务与结果。

## Screening Blocks

Schema 层要求两种正式模式的输入材料已经满足最小形态。材料形态缺失由 API 直接 `422` 阻断。Provider 的 `input_screening` 仍可在材料存在但不可评时返回 `rateable=false`、`continueAllowed=false`，服务端会把上游原因转换为固定的安全错误文案，避免泄露 provider 原始文本或密钥片段。

## Local State

本地开发默认使用 SQLite。需要清空任务、历史和结果时，可以停止 API 后删除本地 DB 文件；随后重启服务会重新创建空库。真实 DeepSeek E2E 命令只应使用占位符，例如 `<redacted-local-key>`，不要把真实 key 写入 README、docs、脚本或测试记录。
