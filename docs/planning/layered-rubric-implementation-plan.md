# 面向网络小说联合投稿包全 LLM Rubric 主线的实施计划

## 文档目的

本文档是 `Phase 1` 的正式实施总入口。它既保留当前真实状态判断，也把路线从单纯的 implementation-prep 扩展为完整交付五段。

## 当前判断

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Not Yet`
- `Delivery-Ready = Not Yet`

## 当前已落地现实

### 已落地

- `packages/schemas/` 已有 `common/input/output/stages` 正式 schema
- `packages/application/` 已有最小 `EvaluationService` 与内存仓库 port
- `apps/api/` 已有最小 FastAPI 路由、错误封装与测试
- `apps/api/tests/` 现有 `31` 条测试与 `compileall` 已通过

### 仍未落地

- `packages/schemas/evals/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `prompts/` 正式资产实例
- `apps/worker/`
- `evals/` runner、report、baseline
- `apps/web/`
- `SQLite` 仓储与历史持久化
- 文件上传受控实现与历史查询完整语义

### 关键现实差距

- `EvaluationService` 仍依赖 `provider-local` / `model-local` 与固定版本常量
- 任务和结果当前只存在于内存仓库
- `/api/history` 的检索、筛选、分页仍未落地
- 上传与解析仍停留在契约层
- `worker` 与 `web` 目录基本仍是空壳

## 五段路线

### `implementation-prep`

目标：补齐最小结构和运行时入口，让主链可继续编码。

对应 mission：

- `I1-I9`

### `runtime completion`

目标：把当前最小样板推进到真实用户任务主链。

对应 mission：

- `R1-R5`

### `evals/worker`

目标：补齐回归闭环、批处理闭环和统一报告闭环。

对应 mission：

- `E1`

### `frontend`

目标：补齐用户闭环。

对应 mission：

- `F1-F2`

### `release/ops`

目标：补齐新环境安装、配置、诊断、回滚与交付门槛。

对应 mission：

- `O1-O2`

## 波次定义

### Wave 1：实现准备

- 清掉 evals schema 空位
- 建立 provider port、prompt runtime 和首批 Prompt 资产骨架
- 让 application 脱离硬编码常量
- 完成 API/worker/evals 的最小接线与 readiness 复审

### Wave 2：运行时主链补齐

- `SQLite` 仓储与 API 进程内执行模型
- 正式 `DeepSeek` adapter
- Prompt runtime 对 Markdown/YAML 资产的真实读取
- 真实 `screening -> rubric -> consistency -> aggregation -> projection`
- 上传解析、历史查询与请求边界错误

### Wave 3：回归闭环

- worker 的 `batch/eval` 模式
- 统一 `EvalReport`
- baseline comparison 输出
- Prompt/Schema/Provider 变更后的受控回归

### Wave 4：前端闭环

- `apps/web` 工程骨架
- adapter/query/form 基线
- 首页、输入页、任务页、结果页、历史页
- 上传 UX、阻断态、失败态与轮询策略

### Wave 5：交付闭环

- env/config/install/start/smoke 文档
- diagnostics 与最小日志字段
- 回滚演练与 release review
- 新环境可按文档完成真实样本验证

## 退出条件

### 进入 `Implementation-Ready`

必须同时满足：

- `packages/schemas/evals/` 正式落地
- provider port、prompt runtime、Prompt 资产可被代码读取
- application 不再写死 provider/prompt 元信息
- API、worker、evals 有最小终止型命令

### 进入 `Delivery-Ready`

必须同时满足：

- 用户任务可真实执行并持久化
- 前端主流程可用
- worker/evals/report/baseline 可执行
- 新环境可完成安装、配置、启动和 smoke
- 重启后历史和结果仍可读

## 当前执行约束

- 不得把 README 或空目录视为已实现
- 不得跳过 `mission-catalog` 与 `mission-dag`
- 不得复活 `pairwise`、多主线评分或前端持有 Prompt
- 不得把多用户、鉴权、实时推送混入当前波次

## 真源优先级

1. 已落地的 `packages/schemas/**/*.py`
2. `docs/contracts/canonical-schema-index.md`
3. `apps/api/contracts/*.md`
4. `docs/contracts/*.md`
5. `docs/architecture/*.md`
6. `docs/planning/devfleet-mission-catalog.md`
7. `docs/planning/devfleet-mission-dag.md`
8. `docs/operations/*.md`
