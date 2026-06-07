# 小说智能打分系统项目说明

## 项目简介

本项目是面向中文网文场景的本地单用户评测工具。核心能力是对用户提交的正文、章节和大纲进行多阶段结构化评价，并输出当前正式结果形态：`overall + axes + optional typeAssessment`。

当前仓库已经进入实现与回归并行维护阶段。后续开发应围绕现有 API、schema、Prompt、worker 和前端页面继续扩展，避免恢复已经退出当前架构的历史目录或结果形状。

## 当前范围

- 官方运行口径：`Windows + PowerShell`
- API：`apps/api` 提供 HTTP 边界，并在进程内执行用户任务
- Web：`apps/web` 提供本地 UI、轮询、历史与结果展示
- Worker：`apps/worker` 只负责 `eval` / `batch`
- 默认存储：`SQLite`，默认路径 `var/novel-evaluation.sqlite3`
- 默认 E2E 基线：deterministic provider；真实 `DeepSeek` 是可选验收路径，默认模型为 `deepseek-v4-pro`

## 仓库结构

### `apps/`

- `apps/api/`：FastAPI 路由、上传解析、错误 envelope 和依赖注入
- `apps/web/`：Next.js App Router 前端和同源 `/api` 代理
- `apps/worker/`：eval / batch CLI

### `packages/`

- `packages/application/`：任务用例、状态推进和评分流水线编排
- `packages/runtime/`：API/worker 共享 runtime 装配、SQLite 持久化和日志
- `packages/schemas/`：输入、阶段、输出、evals 的正式结构契约
- `packages/prompt-runtime/`：Prompt registry/version/body 选择与加载
- `packages/provider-adapters/`：DeepSeek 与 deterministic provider 适配器

### 资产与文档

- `prompts/`：正式 Prompt 资产，只保留当前评分主线
- `evals/`：回归样本、suite、runner、report/baseline 写入模型
- `docs/`：当前正式文档入口，不再保留历史分层目录
- `scripts/`：安装、启动和辅助脚本
- `output/`、`var/`：本地运行产物，不纳入正式源码边界

## 项目规则

### Prompt 治理

- 正式 Prompt 仅从 `prompts/registry`、`prompts/versions`、`prompts/scoring` 加载
- Prompt 版本必须与 schema/rubric 版本一致
- Prompt 不由前端持有或拼接

### JSON 契约

- `packages/schemas` 是正式字段真源
- `apps/web/src/api/contracts.ts` 只是前端消费镜像
- API、worker、evals 都必须遵守同一套结构约束

### 正式评分主线

正式流程固定为：

`input_screening -> type_classification -> rubric_evaluation -> type_lens_evaluation -> consistency_check -> aggregation -> final_projection`

- `consistency_check` 与 `final_projection` 是规则/投影阶段，不发模型请求
- 当前公开结果只保留 `overall + axes + optional typeAssessment`
- 不满足当前 schema 的持久化结果不能伪装成成功结果

### Worker 约定

- `worker eval --dry-run` 和 `worker batch --dry-run` 不要求真实 key
- 不带 `--dry-run` 的真实执行必须配置 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- worker 不承接用户页面任务，不依赖 `apps/api` 内部装配

## 协作原则

- 代码真源优先于解释文档；文档必须跟随当前实现更新
- 新增公开行为时同步更新 README、`docs/runbook.md` 或 `docs/contracts.md`
- 不引入第二套任务状态、错误码、结果 DTO 或 Prompt 选择规则
- 不恢复历史目录、历史结果结构或历史 Prompt 目录

## 推荐阅读顺序

1. `README.md`
2. `docs/runbook.md`
3. `docs/architecture.md`
4. `docs/contracts.md`
5. `docs/request-flow.md`
6. `docs/prompts-and-evals.md`
