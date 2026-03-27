# 本地运行配置与诊断

## 文档目的

本文档冻结 `Phase 1` 已落地实现所使用的最小环境变量集合、默认本地路径和诊断字段集合。

## 环境变量

| 变量 | 作用 | 默认值 | 当前实现说明 |
| --- | --- | --- | --- |
| `NOVEL_EVAL_DEEPSEEK_API_KEY` | DeepSeek API Key | 空 | 为空时回退本地 deterministic adapter，但 `providerId/modelId` 仍保持 `provider-deepseek/deepseek-chat` |
| `NOVEL_EVAL_REQUIRE_REAL_PROVIDER` | 强制真实 Provider 模式 | 空 | 为 `1` 时禁止 fallback；若缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，API 启动直接失败 |
| `NOVEL_EVAL_DB_PATH` | SQLite 文件路径 | `./var/novel-evaluation.sqlite3` | 空值时落到仓库根 `var/novel-evaluation.sqlite3` |
| `NOVEL_EVAL_PROMPTS_DIR` | Prompt 资产根目录 | `./prompts` | 空值时落到仓库根 `prompts/` |
| `NOVEL_EVAL_LOG_LEVEL` | 日志级别 | `INFO` | 为空时按 `INFO`；非法值会在启动期报错 |
| `NOVEL_EVAL_LOG_DIR` | 日志目录 | `./var/logs` | API 与 worker 都会在这里写 `api.log` / `worker.log` |
| `NOVEL_EVAL_API_HOST` | API host | `127.0.0.1` | 启动命令与 web 反向代理默认读取该值 |
| `NOVEL_EVAL_API_PORT` | API port | `8000` | 启动命令与 web 反向代理默认读取该值 |
| `NOVEL_EVAL_WEB_PORT` | web port | `3000` | web 启动命令默认使用该端口 |
| `NOVEL_EVAL_UPLOAD_MAX_BYTES` | 单文件上传上限 | `10485760` | 当前前后端都以 `10 MiB` 作为默认边界 |

## 配置原则

- `Phase 1` 只冻结本地运行配置
- 未列入此表的配置不属于交付必需项
- README、启动命令和应用实现必须使用同一组变量名
- `apps/web` 不直接暴露新的后端地址变量，而是通过同源 `/api` 代理复用 `NOVEL_EVAL_API_HOST / NOVEL_EVAL_API_PORT`
- `apps/web test:e2e` 的 API 子进程会自动注入 `NOVEL_EVAL_REQUIRE_REAL_PROVIDER=1`，因此 E2E 固定要求真实 DeepSeek

## 最小诊断字段

当前 API / worker 主链日志至少应能记录：

- `taskId`
- `stage`
- `requestId`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `errorCode`
- `durationMs`

说明：

- provider 阶段日志会记录 `requestId`
- 生命周期日志会记录 `resultStatus`
- 批处理和回归会复用同一条应用层日志主线，因此同样能带出上述字段

## 诊断规则

最小故障定位路径固定为：

1. 用 `taskId` 定位 `api.log` 或 `worker.log`
2. 读取对应 `stage/promptVersion/schemaVersion/rubricVersion/providerId/modelId`
3. 判断问题属于 `blocked` 还是 `failed`
4. 再决定是重新提交任务、重跑 `worker eval`，还是执行回滚

## 与其它文档的关系

- 执行模型见 `docs/architecture/runtime-execution-and-persistence.md`
- 安装与 smoke 见 `docs/operations/local-installation-and-smoke.md`
- 回滚规则见 `docs/operations/rollback-and-fallback.md`
