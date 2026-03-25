# 前端技术路线

## 技术路线结论

`apps/web` 的正式实现基线固定为：

- `Next.js (App Router) + React + TypeScript`
- 包管理器：`pnpm`
- 样式：`Tailwind CSS + shadcn/ui`
- 服务端状态：`TanStack Query`
- 表单与边界校验：`React Hook Form + Zod`

## 核心实现策略

- `Adapter-First`
- `Mock-First`
- `Polling-First`
- 页面优先于组件体系

## 工程要求

### `F1`

- 搭建 `apps/web` 工程骨架
- 搭建 API client
- 搭建 Query hooks
- 搭建 form/upload 基线

### `F2`

- 首页
- 输入页
- 任务页
- 结果页
- 历史页
- 阻断态与失败态

## 查询策略

- dashboard 聚合读
- task/detail 轮询读
- result 按需读
- history 基于 `q/status/cursor/limit`

## 不采用

- `SSE` 或 `WebSocket` 作为首期前提
- 前端持有 Prompt
- 前端直连 Provider
- 全局 store 复制服务端状态

## 运行命令

- 依赖安装：`pnpm --dir apps/web install`
- 开发启动：`pnpm --dir apps/web dev -- --port 3000`
