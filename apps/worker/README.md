# `apps/worker`

## 模块角色

该模块承载后台执行入口，用于运行耗时任务、批量回归和报告生成，但它不是业务语义真源。

## 输入对象

该模块未来主要消费：

- `EvaluationTask`
- `JointSubmissionRequest` 转化后的任务上下文
- application use case 输入对象
- `EvalCase` / `EvalRecord` 相关执行上下文

## 输出对象

该模块未来主要产出：

- 更新后的 `EvaluationTask`
- 正式 `EvaluationResult`
- `EvalRecord`
- 报告与基线相关产物引用

## 主要职责

- 承接异步执行入口
- 运行正式评分主线
- 运行批量回归与报告生成
- 隔离耗时操作，避免 API 入口承担长时执行

## 不负责

- 发明新的任务状态枚举
- 发明新的错误码语义
- 定义正式 schema 真源
- 绕过 application use case 直接写业务主线

## 依赖关系

该模块依赖：

- `packages/application/`
- `packages/domain/`
- `packages/schemas/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `evals/`

## 错误语义

- 业务阻断必须落到 `completed + blocked`
- 技术失败必须落到 `failed + not_available`
- worker 不得用“重试中”发明新的正式状态枚举
- worker 级重试是执行策略，不是领域状态真源

## Side Effects

允许的 side effects：

- 调用 provider
- 记录任务推进结果
- 写入回归报告产物
- 执行受控批处理

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "后台执行入口|错误语义|验收方式|EvaluationTask|EvalRecord" apps/worker/README.md`

## 当前阶段约束

- 当前不预设复杂分布式调度系统
- 本地部署场景下可先采用轻量、本机可运行的执行方式
- 只要不改写正式契约，可在 worker 不稳定时回退到更简单的执行入口
