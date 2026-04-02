# 本地运行配置与诊断

## 文档目的

本文档冻结当前实现所使用的最小环境变量集合、默认本地路径和诊断字段集合。

## 应用运行环境变量

| 变量 | 作用 | 默认值 | 当前实现说明 |
| --- | --- | --- | --- |
| `NOVEL_EVAL_DEEPSEEK_API_KEY` | DeepSeek API Key | 空 | API 留空时允许只读启动，可查看已有任务/结果/history，但不能创建新分析任务；worker 留空时启动报错 |
| `NOVEL_EVAL_REQUIRE_REAL_PROVIDER` | 已弃用的旧变量 | 空 | API 已忽略该变量；即使设为 `1`，缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时也只会只读启动 |
| `NOVEL_EVAL_DB_PATH` | SQLite 文件路径 | `./var/novel-evaluation.sqlite3` | 空值时落到仓库根 `var/novel-evaluation.sqlite3` |
| `NOVEL_EVAL_PROMPTS_DIR` | 预留变量 | `./prompts` | 当前保留在 `.env.example`，但 API / worker 运行时尚未读取该变量 |
| `NOVEL_EVAL_LOG_LEVEL` | 日志级别 | `INFO` | 为空时按 `INFO`；非法值会在启动期报错 |
| `NOVEL_EVAL_LOG_DIR` | 日志目录 | `./var/logs` | API 与 worker 都会在这里写 `api.log` / `worker.log` |
| `NOVEL_EVAL_API_HOST` | API host | `127.0.0.1` | 启动命令与 web 反向代理默认读取该值 |
| `NOVEL_EVAL_API_PORT` | API port | `8000` | 启动命令与 web 反向代理默认读取该值 |
| `NOVEL_EVAL_WEB_PORT` | web port | `3000` | web 启动命令默认使用该端口 |
| `NOVEL_EVAL_UPLOAD_MAX_BYTES` | 单文件上传上限 | `10485760` | 当前前后端都以 `10 MiB` 作为默认边界 |

## Playwright / 验收专用环境变量

| 变量 | 作用 | 默认值 | 当前实现说明 |
| --- | --- | --- | --- |
| `NOVEL_EVAL_E2E_PROVIDER_MODE` | Playwright provider 模式 | `deterministic` | 支持 `deterministic / startup_key / runtime_key` |
| `NOVEL_EVAL_CAPTURE_README_SCREENSHOT_PATH` | README 截图导出路径 | 空 | 仅在截图更新时使用 |

## 配置原则

- README、启动命令和应用实现必须使用同一组变量名
- `apps/web` 不直接暴露新的后端地址变量，而是通过同源 `/api` 代理复用 `NOVEL_EVAL_API_HOST / NOVEL_EVAL_API_PORT`
- 当 API 启动时缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY`，前端可向本地 API 录入一次性 runtime key；该 key 仅保存在当前 API 进程内，重启或热重载后失效
- 若 API 已在启动期通过环境变量配置 key，前端只展示状态，不支持替换或清空
- runtime key 录入接口只允许本机访问；若请求来自非回环地址或带转发头，API 返回 `FORBIDDEN`
- 已完成任务若关联的结果资源是旧 schema 或损坏 payload，读取时会被标准化为 `completed + not_available`

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

补充：

- `stage` 当前会覆盖：
  - `input_screening`
  - `type_classification`
  - `rubric_evaluation`
  - `type_lens_evaluation`
  - `consistency_check`
  - `aggregation`
  - `final_projection`
- 生命周期日志会额外记录 `resultStatus`
- 任务详情接口本身也可作为诊断入口，用于观察类型识别是否已写回任务元数据

## 诊断规则

最小故障定位路径固定为：

1. 用 `taskId` 定位 `api.log` 或 `worker.log`
2. 读取对应 `stage/promptVersion/schemaVersion/rubricVersion/providerId/modelId`
3. 判断问题属于：
   - 结果阻断
   - provider 失败
   - schema 校验失败
   - 类型回落到 `general_fallback`
4. 再决定是重新提交任务、重跑 `worker eval`，还是执行回滚
