# 本地运行配置与诊断

## 文档目的

本文档冻结 `Phase 1` 已落地实现所使用的最小环境变量集合、默认本地路径和诊断字段集合。

## 环境变量

| 变量 | 作用 | 默认值 | 当前实现说明 |
| --- | --- | --- | --- |
| `NOVEL_EVAL_DEEPSEEK_API_KEY` | DeepSeek API Key | 空 | API 留空时允许只读启动，可查看已有任务/结果/history，但不能创建新分析任务；worker 留空时启动报错 |
| `NOVEL_EVAL_REQUIRE_REAL_PROVIDER` | 已弃用的旧变量 | 空 | API 已忽略该变量；即使设为 `1`，缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时也只会只读启动，不再控制 API 启动成功 |
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
- 当 API 启动时缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，前端可向本地 API 录入一次性 runtime key；该 key 仅保存在当前 API 进程内，重启或热重载后失效
- 若 API 已在启动期通过环境变量配置 key，前端只展示状态，不支持替换或清空
- `apps/web test:e2e` 固定要求真实 DeepSeek；`startup_key` 模式要求 API 子进程启动时即带 key，`runtime_key` 模式则通过 UI 补录一次性 key

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
