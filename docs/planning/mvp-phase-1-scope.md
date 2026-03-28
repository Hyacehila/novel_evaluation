# Phase 1 MVP 范围说明

## 文档目的

本文档冻结小说智能打分系统 `Phase 1` 的最终交付边界。`Phase 1` 不是未来 SaaS 版本，也不是多租户或公网部署版本；它只评估本地单用户、开源可运行交付。

## 交付目标

`Phase 1` 的完整交付判定标准固定为：

- 本地可安装
- 本地可配置
- 可提交真实任务
- 可执行真实评测
- 可读取任务与结果
- 可保留历史并在重启后继续读取
- 可执行受控回归
- 可按文档完成最小回滚与诊断

## 冻结范围

### 部署与运行模型

- 部署形态固定为：开源、本地部署、单用户
- 本地状态存储固定为：`SQLite` 单文件
- 默认数据库路径固定为：`./var/novel-evaluation.sqlite3`
- 用户任务执行模型固定为：`apps/api` 进程内异步执行
- `apps/worker` 固定只负责回归与批处理
- 前端包管理器固定为：`pnpm`

### 输入与提交

正式输入模型固定为联合投稿包，支持：

- `chapters + outline`
- `chapters only`
- `outline only`

正式输入来源固定为：

- 直接文本输入
- 文件上传

`Phase 1` 文件上传格式固定为：

- `TXT`
- `MD`
- `DOCX`

### 后端正式能力

`Phase 1` 必须交付以下主能力：

- `POST /api/tasks` 创建任务
- `GET /api/tasks/{taskId}` 读取任务
- `GET /api/tasks/{taskId}/result` 读取结果资源
- `GET /api/dashboard` 读取首页摘要
- `GET /api/history` 读取历史记录
- 历史记录正式支持 `q/status/cursor/limit`
- 用户任务可从 `queued` 推进到 `completed` 或 `failed`
- 评分主线可产出正式结果或稳定阻断结论

### 正式评分主线

`Phase 1` 唯一正式评分主线固定为：

1. 输入预检查
2. `8` 轴 `LLM rubric` 分点评价
3. 轻量一致性整理
4. 聚合生成 `overallVerdict / overallSummary / platformCandidates / marketFit` 草案
5. 最终结果投影

### 治理与回归能力

`Phase 1` 同时必须具备：

- Prompt 生命周期与版本治理
- Schema 版本治理
- Provider 执行契约
- Evals schema、runner、baseline、report 最小闭环
- 本地安装、启动、smoke、诊断与回滚文档

## 明确不做

以下能力继续排除在 `Phase 1` 外：

- 鉴权
- 多用户与多租户
- `SSE`
- `WebSocket`
- 多 Provider 生产级切换
- 复杂运营后台
- `pairwise` 或多路径评分主线
- 公网 SaaS 部署假设

## 关键边界

### API 语义

- `POST /api/tasks` 固定为非幂等
- 每次成功创建都生成新的 `taskId`
- 传输层重试不承诺去重
- 重复点击提交由前端防抖和提交中禁用处理

### 持久化与恢复

- `EvaluationTask`
- `EvaluationResultResource`
- `EvalRecord`
- `EvalBaseline`
- `EvalReport`

以上对象都属于 `Phase 1` 必需持久化范围。

### 重启语义

- 遗留 `processing` 任务在重启后统一转为 `failed + not_available`
- `Phase 1` 不做自动恢复执行

## 交付产物

`Phase 1` 的正式交付物包括：

- API v0 契约
- 任务状态与错误语义
- 运行时执行与持久化规则
- Provider 执行契约
- 文件上传与摄取边界
- 前端输入、查询、轮询与页面规格
- Prompt 资产格式与运行时选择规则
- Evals schema、runner、baseline、report 契约
- 本地安装、配置、启动、smoke、诊断与回滚文档

## 与前端协作边界

前端继续按以下原则开发：

- `Real-API-First`
- `Adapter-First`
- `Polling-First`

后端必须保证：

- 前端只消费后端校验后的正式结构化结果
- 上传边界、错误码和历史查询语义稳定
- `blocked` 与 `failed` 不返回伪结果

## 未来扩展保留位

以下内容不再作为当前待确认项，而是明确移动到后续阶段：

- 多用户字段
- 鉴权字段
- 工作区或租户隔离字段
- 实时推送能力
- 多 Provider 生产级调度
