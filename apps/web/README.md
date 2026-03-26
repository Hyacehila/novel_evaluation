# `apps/web`

该目录承载用户交互层，当前已落地为 `Next.js App Router + TypeScript + pnpm` 工程。

## 当前已实现

- 工作台首页 `/`
- 新建任务页 `/tasks/new`
- 任务详情页 `/tasks/{taskId}`
- 结果详情页 `/tasks/{taskId}/result`
- 历史记录页 `/history`
- `TanStack Query` 查询层与轮询策略
- `React Hook Form + Zod` 提交表单
- 同源 `/api` 代理到后端 API

## 负责

- 采集标题、正文、大纲或上传文件
- 调用固定 API 路由创建任务
- 轮询任务状态
- 只在 `available` 时展示正式结果
- 支持 `q/status/cursor/limit` 的历史回访

## 不负责

- 持有正式 Prompt
- 直连 Provider
- 解析上传文件正文
- 在 `blocked / not_available / fetch_failed` 时展示伪结果

## 当前使用方式

- 安装：`pnpm --dir apps/web install`
- 开发：`pnpm --dir apps/web dev -- --port 3000`
- 校验：`pnpm --dir apps/web lint && pnpm --dir apps/web test && pnpm --dir apps/web build`
