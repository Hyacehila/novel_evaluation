# 真实 Provider 配置

默认情况下，项目在缺少 `NOVEL_EVAL_DEEPSEEK_API_KEY` 时会回退到本地 deterministic adapter，方便你先验证安装和页面流程。

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

## 3. 可选开启严格真实 Provider 模式

如果你希望 API 在缺少 Key 时直接启动失败，而不是回退本地 adapter，再加上：

```dotenv
NOVEL_EVAL_REQUIRE_REAL_PROVIDER=1
```

## 4. 重启服务

重新执行：

```powershell
.\scripts\run-api.ps1
.\scripts\run-web.ps1
```

通常只有 API 需要读取这个 Key；如果你同时修改了端口或 API 地址，再一起重启 web。

## 什么时候需要真实 Provider

- 你要验证真实模型输出质量
- 你要进行真实体验演示
- 你要执行 `pnpm --dir apps/web test:e2e`

## 什么时候不必急着配置

- 你只是第一次安装仓库
- 你在验证页面、表单和本地持久化
- 你在排查是否是环境安装问题

## 相关变量

- `NOVEL_EVAL_DEEPSEEK_API_KEY`
- `NOVEL_EVAL_REQUIRE_REAL_PROVIDER`
- `NOVEL_EVAL_API_HOST`
- `NOVEL_EVAL_API_PORT`

完整配置表见 `../operations/runtime-configuration-and-diagnostics.md`。
