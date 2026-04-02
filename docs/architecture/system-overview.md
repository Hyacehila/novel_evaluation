# 系统总览

## 系统目标

构建一个面向网络小说投稿评估场景的智能打分系统。当前交付目标仍是开源、本地部署、单用户、可运行的正式版本，而不是未来公网 SaaS。

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
- 在任务页展示输入摘要、运行元信息和类型识别状态
- 在结果页展示总体判断、独立类型评价模块和 `8` 轴 rubric 结果
- 查看 dashboard 与 history

### `apps/api`

- HTTP 入口
- 请求边界校验
- 创建任务与持久化
- 进程内推进用户任务
- 返回任务、结果、dashboard、history
- 在 `type_classification` 完成后把 `novelType / typeClassificationConfidence / typeFallbackUsed` 写回任务元数据

### `apps/worker`

- 执行 `batch`
- 执行 `eval`
- 生成回归 report 与 baseline comparison

### `packages/application`

- 用例编排
- 状态推进
- 调用 Prompt runtime、Provider adapter、Schema 校验
- 组织 `input_screening -> type_classification -> rubric_evaluation -> type_lens_evaluation -> consistency_check -> aggregation -> final_projection`

### `packages/provider-adapters`

- 封装 `DeepSeek API`
- 归一化成功/失败对象
- 提供 provider 元信息与重试边界
- 内置 deterministic adapter，供本地测试和默认 Playwright E2E 使用

### `prompts/` 与 `packages/prompt-runtime`

- Prompt 正文在 `Markdown`
- 元数据在 `YAML`
- runtime 负责按 `stage + inputComposition + evaluationMode + providerId + modelId` 读取、选择和返回 Prompt 绑定
- 当前正式 provider stage 包括 `input_screening`、`type_classification`、`rubric_evaluation`、`type_lens_evaluation`、`aggregation`

### `evals/`

- 样本、case、runner、baseline、report
- 回归与批处理只走 worker/evals 链路

## 正式评分主线

1. `input_screening`
2. `type_classification`
3. `rubric_evaluation`
4. `type_lens_evaluation`
5. `consistency_check`
6. `aggregation`
7. `final_projection`

补充：

- `type_classification` 和 `type_lens_evaluation` 都是独立的 LLM 请求
- `rubric_evaluation` 保留当前通用 `8` 轴，不被类型 lens 取代
- `rubric_evaluation` 当前按 `3 + 3 + 2` 的请求切片执行，再合并回完整 `8` 轴结果
- `aggregation` 同时读取 `screening + type_classification + rubric + type_lens + consistency`
- `final_projection` 输出正式结果 `overall + axes + optional typeAssessment`

## 当前结果与页面语义

- `EvaluationTask` 可在任务执行中提前暴露类型识别信息
- `EvaluationResult` 顶层保留 `overall + axes` 主结构，并新增可选 `typeAssessment`
- 任务详情页固定显示类型识别区域：
  - 未完成类型判断时显示“识别中”
  - 已判断时显示类型 badge、置信度和是否触发兜底
- 结果详情页在总体判断与 `8` 轴之间新增独立“类型评价模块”

## 运行与恢复假设

- 本地状态由 `SQLite` 持久化
- `POST /api/tasks` 创建 `queued` 任务后，由 API 进程内执行器推进
- 进程重启后，遗留 `queued / processing` 任务统一转为 `failed + not_available`
- 已完成任务若关联结果资源已过期、损坏或不满足当前 schema，读取时会降级为 `completed + not_available`
- worker 不接管用户主任务

## 当前排除项

- 多用户 / 多租户
- 鉴权
- `SSE` / `WebSocket`
- 多 Provider 生产级切换
- 复杂运营后台
