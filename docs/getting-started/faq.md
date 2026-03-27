# 常见问题

## 为什么没有配置 API Key 也能跑起来

这是当前仓库的默认设计。缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时，API 会回退到本地 deterministic adapter，方便你先验证安装、前后端联通和 SQLite 持久化。

## fallback 结果和真实模型结果有什么区别

fallback 结果用于本地体验和 smoke，不代表真实模型质量，也不用于正式评审。想看真实模型输出，请配置 `DeepSeek API Key` 并重启 API。

## 页面打开了，但提交任务后一直没有结果

先检查：

- `.\scripts\run-api.ps1` 是否仍在运行
- `.env` 里的 `NOVEL_EVAL_API_HOST / NOVEL_EVAL_API_PORT` 是否和 API 进程一致
- API 控制台是否输出错误日志

如需更多诊断字段和日志定位规则，见 `../operations/runtime-configuration-and-diagnostics.md`。

## worker 是不是必需的

不是。普通用户只需要启动 `api` 和 `web`。`worker` 只负责 `eval` 和 `batch`，不承接页面里提交的用户任务。

## 数据写到哪里了

默认写到：

- SQLite：`./var/novel-evaluation.sqlite3`
- 日志：`./var/logs`

你可以在 `.env` 中修改 `NOVEL_EVAL_DB_PATH` 和 `NOVEL_EVAL_LOG_DIR`。

## 如何清空本地任务和结果

关闭 API 后删除 `./var/novel-evaluation.sqlite3`，再次启动时会自动重新创建空数据库。

## 端口冲突怎么办

修改 `.env` 中的：

- `NOVEL_EVAL_API_PORT`
- `NOVEL_EVAL_WEB_PORT`

然后重新执行 `.\scripts\run-api.ps1` 和 `.\scripts\run-web.ps1`。

## 其他平台能不能跑

理论上可以，但当前文档和官方验证口径以 `Windows + PowerShell` 为主。若你在 macOS 或 Linux 上使用，建议先参考原始命令和配置说明：

- `../operations/local-installation-and-smoke.md`
- `../operations/runtime-configuration-and-diagnostics.md`
