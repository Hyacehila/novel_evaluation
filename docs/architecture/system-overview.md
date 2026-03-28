# 系统总览

## 系统目标

构建一个面向网络小说投稿评估场景的智能打分系统。`Phase 1` 的目标不是未来公网 SaaS，而是一个开源、本地部署、单用户、可运行的正式版本。

## 当前冻结基线

- 前端：`Next.js (App Router) + React + TypeScript + pnpm`
- 后端：`Python 3.13 + uv + FastAPI + Pydantic`
- Provider：`DeepSeek API`
- 编排：`packages/application` 内的 `EvaluationService + ScoringPipeline`
- 本地状态存储：`SQLite`
- 用户任务执行：`apps/api` 进程内异步执行
- worker：仅负责批处理与回归

## 系统组成

### `apps/web`

- 输入或上传正文与大纲
- 读取 provider 状态并在缺少启动期 key 时录入一次性 runtime key
- 创建任务
- 轮询任务状态
- 查看结果和历史

### `apps/api`

- HTTP 入口
- 请求边界校验
- 创建任务与持久化
- 进程内推进用户任务
- 返回任务、结果、dashboard、history

### `apps/worker`

- 执行 `batch`
- 执行 `eval`
- 生成回归 report 与 baseline comparison

### `packages/application`

- 用例编排
- 状态推进
- 调用 Prompt runtime、Provider adapter、Schema 校验
- 组织 `input_screening -> rubric_evaluation -> consistency_check -> aggregation -> final_projection`

### `packages/provider-adapters`

- 封装 `DeepSeek API`
- 归一化成功/失败对象
- 提供 provider 元信息与重试边界

### `prompts/` 与 `packages/prompt-runtime`

- Prompt 正文在 `Markdown`
- 元数据在 `YAML`
- runtime 负责按 `stage + inputComposition + evaluationMode + providerId + modelId` 读取、选择和返回 Prompt 绑定

### `evals/`

- 样本、case、runner、baseline、report
- 回归与批处理只走 worker/evals 链路

## 正式评分主线

1. 输入预检查
2. `8` 轴 `LLM rubric` 分点评价
3. 轻量一致性整理
4. 聚合生成 `overallVerdictDraft / overallSummaryDraft / platformCandidates / marketFitDraft`
5. 最终结果投影为 `overall + axes`

这是当前仓库唯一正式评分路径。

补充：

- `rubric_evaluation` 当前按 `3 + 3 + 2` 的请求切片执行，再合并回完整 `8` 轴结果
- `aggregation` 不再把旧四维骨架作为正式输出对象
- `final_projection` 会把 rubric 轴结果直接映射为结果页展示的 `axes`，并结合一致性信号推导 `overall.score`

## 运行与恢复假设

- 本地状态由 `SQLite` 持久化
- `POST /api/tasks` 创建 `queued` 任务后，由 API 进程内执行器推进
- 进程重启后，遗留 `queued / processing` 任务统一转为 `failed + not_available`
- 已完成任务若关联结果资源已过期或损坏，读取时会降级为 `completed + not_available`
- worker 不接管用户主任务

## 当前排除项

- 多用户 / 多租户
- 鉴权
- `SSE` / `WebSocket`
- 多 Provider 生产级切换
- 复杂运营后台
