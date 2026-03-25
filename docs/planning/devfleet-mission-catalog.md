# DevFleet Mission Catalog

## 文档目的

本文档定义 `Phase 1` 的正式 mission 清单。它既保留当前 `I1-I9` 的 implementation-prep 波次，也补齐运行时、前端、回归和交付波次。

## Mission 状态词表

- `active_now`：当前可直接下发
- `blocked_by_impl`：被 `I` 组阻塞
- `blocked_by_runtime`：被 `R` 组阻塞
- `blocked_by_fullstack`：被前置主链阻塞
- `future_only`：本轮不进入执行

## 总表

| Mission | 状态 | 目标 | 主要输入 | 主要输出 | depends_on |
| --- | --- | --- | --- | --- | --- |
| `I1` | `active_now` | 落地 `packages/schemas/evals/` 正式 schema | `docs/contracts/canonical-schema-index.md`、`evals/*.md` | `EvalCase`、`EvalRecord`、`EvalBaseline`、`EvalReport` schema | 无 |
| `I2` | `active_now` | 落地最小 provider port 与本地 adapter | `docs/contracts/provider-execution-contract.md`、`packages/provider-adapters/README.md` | port、占位 adapter、错误归一化 | 无 |
| `I3` | `active_now` | 落地 prompt runtime 读取接口 | `docs/prompting/prompt-lifecycle.md`、`packages/prompt-runtime/README.md` | registry/version/body 读取器 | 无 |
| `I4` | `active_now` | 落地首批 Prompt 资产骨架 | `prompts/*.md` | 最小 Markdown/YAML 资产实例 | `I3` |
| `I5` | `blocked_by_impl` | application 通过 port 消费 prompt/provider | `I2`、`I3`、`packages/application` | 去硬编码化 service | `I2`、`I3` |
| `I6` | `blocked_by_impl` | API 依赖注入与 DTO 对齐 | `apps/api/contracts/*.md`、`I5` | API 接线与测试调整 | `I5` |
| `I7` | `blocked_by_impl` | worker 最小执行入口 | `apps/worker/README.md`、`I5` | worker CLI 骨架 | `I5` |
| `I8` | `blocked_by_impl` | eval runner / report 输出骨架 | `evals/*.md`、`I1`、`I4` | runner/report/baseline 骨架 | `I1`、`I4` |
| `I9` | `blocked_by_impl` | implementation-prep 复审 | `I1-I8` | `Implementation-Ready` 结论 | `I6`、`I7`、`I8` |
| `R1` | `blocked_by_impl` | `SQLite` 仓储与 API 进程内执行模型 | `docs/architecture/runtime-execution-and-persistence.md` | `SQLite` repo、重启语义、进程内执行器 | `I5`、`I6` |
| `R2` | `blocked_by_impl` | 正式 `DeepSeek` provider 契约与 adapter | `docs/contracts/provider-execution-contract.md`、`docs/architecture/provider-abstraction.md` | 正式 adapter、失败映射 | `I2`、`I5` |
| `R3` | `blocked_by_impl` | Prompt runtime 与 Markdown/YAML 资产读取 | `docs/prompting/prompt-lifecycle.md`、`prompts/*.md` | 正式 runtime 选择、加载、守卫 | `I3`、`I4` |
| `R4` | `blocked_by_impl` | 真实评分主线运行时节点 | `docs/contracts/rubric-stage-contracts.md`、`docs/architecture/scoring-pipeline.md` | screening/rubric/consistency/aggregation/projection 实现 | `R2`、`R3`、`R1` |
| `R5` | `blocked_by_impl` | 上传解析、历史筛选分页与请求边界文件错误 | `docs/contracts/file-upload-and-ingestion-boundary.md`、`apps/api/contracts/*.md` | multipart 支持、解析器、history query | `R1`、`I6` |
| `E1` | `blocked_by_runtime` | worker/evals/统一 `EvalReport` 闭环 | `docs/architecture/evals-framework.md`、`evals/*.md` | batch/eval CLI、统一报告、baseline comparison | `R2`、`R3`、`R4`、`R5` |
| `F1` | `blocked_by_runtime` | `apps/web` 工程骨架、adapter/query/form 基线 | 前端架构与契约文档 | web 工程骨架、API client、query hooks | `I6`、`R5` |
| `F2` | `blocked_by_runtime` | 首页、输入页、任务页、结果页、历史页与上传 UX | 前端页面与查询文档 | 用户闭环页面与状态处理 | `F1`、`R4`、`R5` |
| `O1` | `blocked_by_fullstack` | env/config/install/start/smoke 文档与命令对齐 | `docs/operations/*.md`、`R1-R5`、`F2` | 安装、启动、smoke、配置入口 | `R1`、`R5`、`F2` |
| `O2` | `blocked_by_fullstack` | diagnostics/rollback/release review 与最终门槛复审 | `docs/operations/*.md`、`E1` | 诊断、回滚、release review | `E1`、`O1` |

## 组别说明

### `I` 组：Implementation-Prep

作用：补齐最小结构、port 和资产骨架，让仓库进入可继续编码的状态。

### `R` 组：Runtime Completion

作用：补齐用户任务主链，包括持久化、正式 provider、正式 prompt runtime、真实评分节点和上传/历史边界。

### `E` 组：Evals / Worker

作用：把 `worker`、runner、report、baseline 串成受控回归闭环。

### `F` 组：Frontend

作用：补齐 `apps/web` 的工程骨架和页面闭环。

### `O` 组：Release / Ops

作用：补齐环境变量、安装、启动、smoke、诊断、回滚和最终 release review。

## 关键 mission 说明

### `R1` SQLite 仓储与 API 进程内执行模型

- 冻结范围：`SQLite` 单文件、`NOVEL_EVAL_DB_PATH`、`queued -> processing -> completed/failed`
- 非目标：不引入消息队列，不把用户任务转交 `worker`
- 验收：重启后历史与结果仍可读；遗留 `processing` 任务转为 `failed + not_available`

### `R2` DeepSeek provider 契约与正式 adapter

- 冻结范围：`ProviderExecutionRequest/Success/Failure`
- 非目标：多 Provider 生产级切换
- 验收：Provider 失败能映射到 `PROVIDER_FAILURE / TIMEOUT / DEPENDENCY_UNAVAILABLE / CONTRACT_INVALID`

### `R3` Prompt runtime 与 Markdown/YAML 资产读取

- 冻结范围：`prompts/scoring/**/*.md`、`prompts/registry/*.yaml`、`prompts/versions/**/*.yaml`
- 非目标：复杂模板系统
- 验收：按 `stage -> inputCompositionScope -> evaluationModeScope -> providerScope -> modelScope -> enabled` 选择资产

### `R4` 真实评分主线运行时节点

- 冻结范围：真实 `screening/rubric/consistency/aggregation/final_projection`
- 非目标：多路径评分、`pairwise`
- 验收：至少一个真实样本可输出正式结果或稳定阻断

### `R5` 上传解析与历史检索边界

- 冻结范围：`TXT/MD/DOCX`、`chaptersFile/outlineFile`、`q/status/cursor/limit`
- 非目标：复杂批量上传、多章节自动拆分
- 验收：文件错误码与历史查询语义对齐 API/前端契约

### `E1` worker/evals/统一 EvalReport 闭环

- 冻结范围：`reportType = execution_summary | baseline_comparison`
- 非目标：复杂可视化评测后台
- 验收：Prompt/Schema/Provider 变化可触发一次受控回归并写出结构化 report/baseline

### `F1-F2`

- `F1` 负责工程壳、adapter、query、form 基线
- `F2` 负责用户页面与 UX
- 验收：用户可完成创建任务、轮询状态、查看结果、查看历史

### `O1-O2`

- `O1` 负责安装、env、启动与 smoke
- `O2` 负责 diagnostics、rollback、release review
- 验收：新环境可按文档完成真实样本验证，失败路径可定位

## 下发规则

- 当前允许下发：`I1-I4`
- `I5-I9` 需等待上游 `I` 组完成
- `R/E/F/O` 组不得提前下发
- 每个 mission 仍必须遵守“单一真源、单一验收标准、单一文件集”原则
