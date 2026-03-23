# 小说智能打分系统项目说明

## 项目简介

本项目是一个面向小说文本评审场景的智能打分系统仓库，核心能力是使用 `LLM as Judge` 对用户提交的小说开篇、章节、大纲或相关文本进行结构化评价。

当前仓库处于**结构构建与工程初始化阶段**，目标是先完成目录边界、文档治理、Prompt 治理、评测体系和后端基础工程的搭建，而不是立即进入业务开发。

## 当前阶段定位

- 当前重点是结构建设、初始化与协作规则固化
- 当前不应将研究产物误当作正式源码
- 当前后端 Agent 逻辑的实现基线确定为 Python
- Python 环境与依赖管理统一使用 `uv`
- Python 版本基线为 `3.13`

## 仓库结构

### `apps/`

用于放置可运行的应用入口。

- `apps/web/`：用户交互层与结果展示层
- `apps/api/`：后端接口与 Agent 服务入口
- `apps/worker/`：异步任务、批处理、回归执行入口

### `packages/`

用于放置可复用的核心能力。

- `packages/domain/`：领域模型与评分对象
- `packages/application/`：评分流程编排
- `packages/provider-adapters/`：模型供应商适配
- `packages/schemas/`：正式结构契约
- `packages/prompt-runtime/`：Prompt 运行时治理能力
- `packages/shared/`：配置、日志、错误与工具
- `packages/sdk/`：稳定客户端接口与共享类型

### `prompts/`

用于放置正式 Prompt 资产。

- Prompt 只允许在后端控制范围内治理和使用
- Prompt 必须版本化、可追踪、可回滚
- Prompt 不能由前端直接持有和拼接

### `evals/`

用于放置评测样本、用例、基线与报告。

### `docs/`

用于放置规划、架构、契约、决策、研究与运维文档。

### `output/`

用于放置抓取、分析、快照和临时产物。

- `output/playwright/` 永久视为研究/抓取产物区
- 该目录不纳入正式源码实现边界

### `scripts/`

用于放置仓库维护、结构检查和评测辅助脚本。

## 项目规则

### Prompt 治理

- 正式 Prompt 仅允许由后端治理
- Prompt 资产应放在 `prompts/`
- Prompt 的使用必须与 Schema 和 Evals 共同考虑

### JSON 契约

- 模型输出必须以严格 JSON 为目标
- 正式结构应以 `packages/schemas/` 为唯一真源
- API、Worker、Evals 都必须遵守同一套结构约束

### 研究产物边界

- `output/playwright/*` 仅作研究用途
- 正式业务逻辑不得直接依赖研究产物文件
- 如需吸收研究结论，应转写到 `docs/` 或正式结构文档中

### Python 与执行约定

- 后端 Agent 逻辑采用 Python 实现
- Python 项目统一使用 `uv`
- 运行 Python 命令统一使用 `uv run`
- Python 版本基线为 `3.13`
- 后端 Python 工程默认放在 `apps/api/`

## 协作原则

- 先结构、再契约、后实现
- 新增目录时优先补充 `README.md` 或其它说明型占位文件
- 生成物、缓存和虚拟环境不纳入版本控制
- 如果后续在子目录新增 `CLAUDE.md`，其作用域遵循 Claude Code 的层级规则

## 当前不应做的事情

- 不要将仓库整体误写成单一技术栈项目
- 不要在没有正式契约和评测边界前直接扩张业务代码
- 不要把 `output/` 中的研究产物迁入 `apps/` 或 `packages/`

## 推荐阅读顺序

1. `README.md`
2. `docs/planning/novel-scoring-system-master-plan.md`
3. `docs/planning/repo-restructure-task-list.md`
4. `docs/architecture/repository-layout.md`
5. `docs/contracts/json-contracts.md`
6. `docs/decisions/ADR-001-repo-structure.md`
7. `docs/decisions/ADR-002-prompt-governance.md`
8. `docs/decisions/ADR-003-output-artifacts-boundary.md`
