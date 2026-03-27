# `apps/api/src`

该目录承载后端服务实现代码。

## 当前结构

- `api/`：FastAPI 应用包，包含应用入口、路由、依赖装配、SQLite 仓储和上传解析

## 约束

- 服务端实现应遵守 `packages/schemas/` 与 `prompts/` 的边界约束
- 接口层不应在这里重新定义正式 Schema、Prompt 正文或前端专用 View Model
