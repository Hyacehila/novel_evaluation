# `apps`

该目录用于承载可运行的应用入口。

## 子目录

- `web/`：用户交互与结果展示入口
- `api/`：后端接口入口，接收请求并在进程内执行用户任务
- `worker/`：批处理与回归入口，不承接页面提交的用户任务

## 常用命令

- API：`uv run --project apps/api uvicorn api.app:app --reload --host 127.0.0.1 --port 8000`
- web：`pnpm --dir apps/web dev -- --hostname 127.0.0.1 --port 3000`
- worker eval：`uv run --project apps/worker worker eval --help`
- worker batch：`uv run --project apps/worker worker batch --help`

## 原则

- 运行入口放在 `apps/`
- 可复用核心能力应下沉到 `packages/`
- `apps/api` 与 `apps/worker` 应复用同一套应用层、Prompt Runtime、Provider Adapter 与 Schema 约束
