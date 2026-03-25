# Rollback / Fallback 主文档

## 文档角色

本文档定义当前仓库在 `DevFleet-Ready` 阶段的最小回滚、降级与失败退出策略。

它负责回答：

- Prompt、Schema、Provider、Worker、Evals 变化失败后如何退出
- 哪些问题属于回滚，哪些属于降级、阻断或技术失败
- 当前仓库哪些层已经落地，哪些层还只是合同 README

## 当前前提

- 当前仓库以本地单用户、开源、本机联调为前提
- `packages/schemas/`、`packages/application/`、`apps/api/` 与 `apps/api/tests/` 已落地最小基线
- `prompts/`、`evals/`、`packages/provider-adapters/`、`packages/prompt-runtime/`、`packages/sdk/`、`scripts/` 仍以 README 合同和占位目录为主
- 当前 `packages/application/services/evaluation_service.py` 使用本地占位元数据 `provider-local` / `model-local`
- 当前 `apps/worker/` 只有 README 级合同，没有正式执行入口代码

## 总原则

- 回滚优先恢复“可解释、可追踪、可消费”的稳定状态
- 不允许通过删除失败记录来伪装问题不存在
- 业务阻断与技术失败必须分层处理
- README 合同层与运行时代码层都必须能指出上一个稳定点

## 一、Prompt 回滚

### 适用场景

- Prompt 治理文档变更导致阶段边界漂移
- Prompt 版本约束、registry 启用规则或回归要求写错
- 未来正式 Prompt 资产落地后，版本更新引发语义或结构退化

### 当前仓库现实

- 当前 `prompts/` 下还没有正式 Prompt 正文实例、registry 实例或 version 记录实例
- 目前可回滚的对象主要是：
  - `prompts/README.md`
  - `prompts/scoring/README.md`
  - `prompts/registry/README.md`
  - `prompts/versions/README.md`

### 最小要求

- 回退时同步恢复 Prompt 目录说明、registry 约束和 version 说明
- 不允许只改单个 README 导致 Prompt 真源解释分裂
- 正式资产落地后，必须通过 `promptVersion` 指向前一稳定版本

## 二、Schema 回滚

### 适用场景

- 字段或枚举变更引发破坏性兼容问题
- 结果结构无法被前端、API 或 Evals 稳定消费
- 阶段契约变更引发主线对象边界漂移

### 最小要求

- 明确前一 `schemaVersion`
- 记录是否属于破坏性变更
- 同步检查：
  - `docs/contracts/json-contracts.md`
  - `docs/contracts/rubric-stage-contracts.md`
  - `apps/api/contracts/job-lifecycle-and-error-semantics.md`
  - `docs/contracts/frontend-minimal-api-assumptions.md`
  - `docs/contracts/canonical-schema-index.md`

### 回滚动作

- 恢复前一字段语义与枚举集合
- 恢复前一 API / 前端假契约解释
- 标记失败变更需要重新进入审查，而不是偷偷覆盖

## 三、Provider Fallback

### 适用场景

- 未来正式 Provider 接入失败
- Provider 文档、版本约束、回归口径或适配边界写错
- Provider 输出稳定性或可用性退化

### 当前仓库现实

- 当前仓库还没有真正落地 `packages/provider-adapters/` 实现
- 当前应用层只写入占位元数据：
  - `providerId = provider-local`
  - `modelId = model-local`
- 因此当前不存在“正式外部 Provider 自动切换”能力

### 当前策略

- Provider 相关改动失败时，优先回到本地占位基线，而不是临时发明第二套 Provider 选择逻辑
- 不允许在 `apps/api/` 或 `packages/application/` 里直接塞入临时 SDK 细节作为长期方案
- 一旦未来正式接入外部 Provider，必须连同 Prompt registry、Evals 基线和回滚说明一起冻结

## 四、Worker 回滚与绕行

### 适用场景

- `apps/worker/` 新增执行入口失败
- 批量回归脚本与 worker 路径冲突
- 长时执行路径改变了任务语义或错误语义

### 当前仓库现实

- `apps/worker/` 当前只有 README，没有正式执行入口代码
- 当前稳定基线仍是 API 进程内调用 `packages/application/` 的最小路径

### 当前策略

- worker 相关尝试失败时，应回退到当前 API / application 的进程内基线
- worker 不是领域真源，不得发明新的任务状态或错误枚举
- worker 重试只属于执行策略，不属于正式状态真源

## 五、结果阻断处理

### 适用场景

- 联合输入不可评
- 单侧输入不足且不满足正式展示条件
- 跨输入冲突不可归一化
- 正式结果不满足展示条件

### 当前策略

- 进入 `completed + blocked`
- 返回稳定 `errorCode` / `errorMessage`
- 不生成伪正式结果正文
- 前端停留任务页或阻断态，不进入正常结果页

### 说明

- 阻断不是技术失败
- 阻断也不是“给一个低分结果凑合展示”

## 六、Evals / Baseline 回退

### 适用场景

- Evals README 合同写错，导致回归对象或报告边界漂移
- 未来样本、case、baseline、report 实例落地后出现回归结论退化
- Prompt / Schema / Provider 变化后评测口径失真

### 当前仓库现实

- `evals/` 当前只有 README 与 `.gitkeep` 占位目录
- `evals/cases/`、`evals/baselines/`、`evals/reports/` 还没有正式实例文件
- `packages/schemas/evals/` 也仍是 README 级说明

### 最小要求

- 回退时先恢复治理文档，再恢复未来的实例记录
- 保留旧 baseline / report 的可追踪引用
- 不允许用“直接覆盖旧报告”掩盖新版本退化

## 七、文档回退

### 适用场景

- 新文档引入第二套真源
- 状态、错误、字段或对象边界被错误重写
- mission 上游文档被扩大解释导致并行开发冲突

### 当前策略

以下文档仍是当前收口阶段的调度真源：

- `docs/planning/layered-rubric-implementation-plan.md`
- `docs/planning/devfleet-mission-catalog.md`
- `docs/planning/devfleet-mission-dag.md`
- `docs/contracts/canonical-schema-index.md`

若下游文档与这些主文档冲突，应优先回退下游解释，而不是反向改写总计划。

## 八、恢复顺序建议

当一次变化同时影响多个层面时，建议按以下顺序恢复：

1. 恢复 schema / 状态真源
2. 恢复 API 契约与前端最小消费假设
3. 恢复 Prompt registry / versions / scoring 治理说明
4. 恢复 Evals baseline / report 口径
5. 最后再恢复 worker、scripts 与模块 README

## 当前不包含的内容

本文档当前不定义：

- 自动化灰度发布系统
- 线上流量切换策略
- 多区域容灾方案
- 多租户权限恢复流程
- 外部 Provider 自动切换编排

## 完成标准

满足以下条件时，可认为当前仓库已有最小回滚主文档：

- Prompt、Schema、Provider、Worker、Evals 都有明确失败退出语义
- 已落地层与 README 合同层不再混为一谈
- 阻断与失败不再混淆
- DevFleet 后续 mission 能判断失败后应该先恢复哪一层真源
