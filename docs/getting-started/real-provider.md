# 真实 Provider 配置

默认情况下，项目在缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时，API 仍可只读启动，方便你先验证安装、页面流程和历史读取；但此时不能创建新的分析任务。

如果你准备使用真实 `DeepSeek API`，按下面步骤配置。

## 1. 准备配置文件

如果仓库根目录还没有 `.env`：

```powershell
Copy-Item .env.example .env
```

## 2. 填入 API Key

在 `.env` 中设置：

```dotenv
NOVEL_EVAL_DEEPSEEK_API_KEY=<your-real-key>
```

## 3. 选择配置方式

你可以按两种方式让 API 进入可分析状态：

### 方式 A：启动期环境变量

在 `.env` 中配置 `NOVEL_EVAL_DEEPSEEK_API_KEY`，然后重启 API。此时 UI 只展示“已配置”状态，不支持在页面里替换或清空该 Key。

### 方式 B：前端录入一次性 runtime key

如果 API 启动时没有 provider key，前端会在新建任务页提供录入口。录入后该 key 仅保存在当前 API 进程内，可立即用于创建分析任务；一旦 API 重启或热重载，该 key 会失效，需要重新录入。

`NOVEL_EVAL_REQUIRE_REAL_PROVIDER` 已弃用，不再控制 API 是否能成功启动；即使设为 `1`，API 在缺少 key 时也只会以只读模式启动。

## 4. 重启服务

重新执行：

```powershell
.\scripts\run-api.ps1
.\scripts\run-web.ps1
```

通常只有 API 需要读取这个 Key；如果你同时修改了端口或 API 地址，再一起重启 web。worker 仍要求在启动前通过环境变量提供 `NOVEL_EVAL_DEEPSEEK_API_KEY`。

## 什么时候需要真实 Provider

- 你要验证真实模型输出质量
- 你要进行真实体验演示
- 你要执行 `pnpm --dir apps/web test:e2e`

## 什么时候不必急着配置

- 你只是第一次安装仓库
- 你在验证页面、表单、本地持久化以及历史读取
- 你暂时只需要只读查看已有数据
- 你在排查是否是环境安装问题

## 相关变量

- `NOVEL_EVAL_DEEPSEEK_API_KEY`
- `NOVEL_EVAL_REQUIRE_REAL_PROVIDER`（已弃用，不再控制 API 启动成功）
- `NOVEL_EVAL_API_HOST`
- `NOVEL_EVAL_API_PORT`

完整配置表见 `../operations/runtime-configuration-and-diagnostics.md`。
