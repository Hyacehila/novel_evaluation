# 本地安装与 Smoke

## 文档目的

本文档冻结 `Phase 1` 完整交付态的安装、启动和 smoke 命令。后续实现必须对齐这些命令和步骤。

## 安装命令

- API：`uv sync --project apps/api`
- worker：`uv sync --project apps/worker`
- web：`pnpm --dir apps/web install`

## 启动命令

### API

`uv run --project apps/api uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000`

### web

`pnpm --dir apps/web dev -- --port 3000`

### worker batch

`uv run --project apps/worker python -m worker.main batch`

### worker eval

`uv run --project apps/worker python -m worker.main eval`

说明：

- 当前仓库未全部落地前，以上命令属于正式交付目标命令
- 环境变量生效后，应用实现应优先读取配置而不是硬编码端口

## 启动顺序

1. 配置环境变量
2. 启动 API
3. 启动 web
4. 需要回归或批处理时再启动 worker

## Smoke 场景

完整交付前至少跑通以下场景：

### 1. 直接输入成功流

- 提交 `title + chapters + outline`
- 任务完成
- 结果可读取

### 2. 文件上传流

- 通过 `chaptersFile` 或 `outlineFile` 提交
- 后端完成解析
- 结果或阻断结论可读取

### 3. 阻断流

- 任务进入 `completed + blocked`
- 结果接口不返回伪结果

### 4. 失败流

- 任务进入 `failed + not_available`
- 可读取 `errorCode` 与最小诊断信息

### 5. 重启后历史可读流

- 任务完成并写入持久化
- 重启 API 后仍可读取 task/result/history

## 交付前最小命令检查

- `git diff --check`
- `uv run --project apps/api python -m compileall .\\apps\\api\\src .\\apps\\api\\tests .\\packages`
- `uv run --project apps/api pytest .\\apps\\api\\tests`
