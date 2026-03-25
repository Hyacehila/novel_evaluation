# 本地运行配置与诊断

## 文档目的

本文档冻结 `Phase 1` 的最小环境变量集合、默认本地路径和诊断字段集合。

## 环境变量

| 变量 | 作用 | 默认值 |
| --- | --- | --- |
| `NOVEL_EVAL_DEEPSEEK_API_KEY` | DeepSeek API Key | 无，必填 |
| `NOVEL_EVAL_DB_PATH` | SQLite 文件路径 | `./var/novel-evaluation.sqlite3` |
| `NOVEL_EVAL_LOG_LEVEL` | 日志级别 | `INFO` |
| `NOVEL_EVAL_API_HOST` | API host | `127.0.0.1` |
| `NOVEL_EVAL_API_PORT` | API port | `8000` |
| `NOVEL_EVAL_WEB_PORT` | web port | `3000` |
| `NOVEL_EVAL_UPLOAD_MAX_BYTES` | 单文件上传上限 | `10485760` |
| `NOVEL_EVAL_PROMPTS_DIR` | Prompt 资产根目录 | `./prompts` |
| `NOVEL_EVAL_LOG_DIR` | 日志目录 | `./var/logs` |

## 配置原则

- `Phase 1` 只冻结本地运行配置
- 未列入此表的配置不属于交付必需项
- 命令、README 和应用实现必须使用同一组变量名

## 最小诊断字段

所有 API、worker、eval runner 日志至少应能记录：

- `requestId`
- `taskId`
- `evalCaseId`
- `stage`
- `promptId`
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- `taskStatus`
- `resultStatus`
- `errorCode`
- `durationMs`

## 诊断规则

- `requestId` 是单次请求级关联键
- `taskId` 是用户任务级关联键
- `evalCaseId` 只在回归或批处理场景出现
- `errorCode` 必须与正式错误码集合一致
- `durationMs` 统一为毫秒

## 日志与故障定位

最小故障定位路径固定为：

1. 用 `taskId` 或 `requestId` 定位日志
2. 读取对应 `stage/promptVersion/schemaVersion/providerId/modelId`
3. 判断任务属于 `blocked` 还是 `failed`
4. 再决定是否需要重新提交任务或执行回归

## 与其它文档的关系

- 执行模型见 `docs/architecture/runtime-execution-and-persistence.md`
- 安装与 smoke 见 `docs/operations/local-installation-and-smoke.md`
- 回滚规则见 `docs/operations/rollback-and-fallback.md`
