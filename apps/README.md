# `apps`

该目录用于承载可运行的应用入口。

## 当前子目录

- `web/`：用户交互与结果展示入口
- `api/`：后端接口入口，按 `FastAPI + Pydantic` 基线实现
- `worker/`：异步任务、批量回归与后台执行入口

## 本地运行假设

- 项目当前按开源项目本地部署方式设计
- 用户本机启动 `apps/web` 与 `apps/api` 后即可联调和使用
- 如需异步执行或回归任务，可在本机额外启动 `apps/worker`

## 原则

- 运行入口放在这里
- 可复用核心能力应下沉到 `packages/`
- 不让应用层承担过多共享逻辑
- `apps/api` 与 `apps/worker` 应复用同一套应用层、Prompt Runtime、Provider Adapter 与 Schema 约束
