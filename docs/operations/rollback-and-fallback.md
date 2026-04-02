# Rollback / Fallback 主文档

## 文档角色

本文档定义当前仓库的最小回滚、降级与失败退出策略。

## 当前前提

- `packages/schemas/`、`packages/application/`、`packages/provider-adapters/`、`packages/prompt-runtime/`、`apps/api/`、`apps/worker/`、`evals/`、`apps/web/` 都已进入真实实现态
- 正式主链固定为七段：`input_screening -> type_classification -> rubric_evaluation -> type_lens_evaluation -> consistency_check -> aggregation -> final_projection`
- 用户任务真源固定为 SQLite；回归与批处理产物真源固定为 `evals/reports/*.json` 与 `evals/baselines/*.json`
- 未配置 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时，API 允许只读启动，而不是停机；worker 仍要求启动期 key

## 总原则

- 回滚优先恢复“可解释、可追踪、可消费”的稳定状态
- 不允许通过删除失败记录来伪装问题不存在
- 业务阻断、类型兜底与技术失败必须分层处理
- 文档与命令必须一起回滚，不能只退代码不退操作口径

## 一、Prompt 回滚

适用场景：

- Prompt registry 选型错误
- `promptVersion` 更新导致阶段输出退化
- Prompt 正文与版本元数据不一致

最小动作：

- 回退 `prompts/registry/*`、`prompts/versions/*` 和对应 Markdown 正文
- 恢复前一稳定 `promptVersion`
- 重新执行 `worker eval --suite <name> --baseline-id <id>`

## 二、Schema 回滚

适用场景：

- 字段或枚举变更引发兼容性破坏
- API / web / evals 无法稳定消费结果结构

最小动作：

- 回退 `packages/schemas/**/*.py`
- 同步回退 `docs/contracts/canonical-schema-index.md`
- 重新跑 API、worker、web 全部门禁

## 三、类型兜底与类型阶段失败

需要区分两类情况：

### 1. 低置信类型判定

- 不属于任务失败
- 按 `general_fallback` 继续执行后续 lens
- 任务与结果仍可成功完成

### 2. 类型阶段 provider / schema 失败

- 属于正式阶段失败
- 不做静默跳过
- 任务进入 `failed + not_available`

## 四、Provider 配置与只读降级

适用场景：

- DeepSeek API 不可用
- provider 输出结构失真
- API Key 缺失或依赖超时

当前策略：

- API 缺少启动期 key 时允许只读启动，保留 dashboard/history/既有任务与结果读取能力
- API 缺少 key 时，新分析任务创建统一被拒绝，需先配置启动期 key，或由前端录入一次性 runtime key
- runtime key 仅保存在当前 API 进程内，重启或热重载后失效
- 若 API 启动时已配置环境变量 key，UI 只展示状态，不支持替换或清空
- worker 不支持 runtime key，启动前必须设置 `NOVEL_EVAL_DEEPSEEK_API_KEY`
- `NOVEL_EVAL_REQUIRE_REAL_PROVIDER` 已弃用，不再控制 API 启动成功
- 若 provider 输出不满足 contract，统一映射为 `failed + not_available`

## 五、Worker 回滚与绕行

适用场景：

- `worker eval` 或 `worker batch` 接线失败
- 回归报告写出格式错误

当前策略：

- worker 失败时，不影响用户任务主链
- `worker eval` 与 `worker batch` 都必须继续复用 `packages/application` 的同一条评分主线
- 如回归链路故障，可先保留 API / web 主链，再单独回退 worker 改动

## 六、结果阻断处理

适用场景：

- 联合输入不可评
- 单侧输入不足
- 跨输入冲突不可归一化
- 正式结果不满足展示条件

当前策略：

- 固定进入 `completed + blocked`
- 返回稳定 `errorCode / errorMessage`
- `GET /api/tasks/{taskId}/result` 不返回伪结果
- web 任务页和结果页都只展示阻断态

## 七、文档回退

若以下文档与代码现实冲突，应先回退文档到当前实现：

- `README.md`
- `docs/architecture/*.md`
- `docs/contracts/*.md`
- `docs/getting-started/*.md`
- `docs/operations/*.md`

## 八、恢复顺序建议

1. 恢复 schema / 状态真源
2. 恢复 Prompt / Provider 版本
3. 恢复 API / worker / web 接线
4. 恢复 evals baseline / report 口径
5. 最后恢复 README 与运维文档
