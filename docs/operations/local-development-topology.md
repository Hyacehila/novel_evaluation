# 本地开发与部署拓扑

## 文档目的

本文档用于说明项目当前“开源项目、本地部署、本机联调”的运行假设，帮助开发者和未来用户理解 `apps/web`、`apps/api`、`apps/worker` 与外部模型 Provider 之间的关系。

本文档不负责：

- 定义具体端口号
- 定义具体环境变量命名
- 定义生产级集群部署方案
- 替代各应用目录下的启动说明

## 当前部署定位

当前项目优先服务以下场景：

- 开发者本地开发
- 用户在自己的电脑上部署
- 本机启动前端与后端完成联调
- 本机执行回归与验证任务

当前不以内置以下假设为前提：

- 公网多租户服务
- 高并发流量入口
- 负载均衡集群
- 分布式任务系统前置依赖
- 实时推送基础设施

## 组件拓扑

### 1. `apps/web`

职责：

- 提供用户输入界面与结果展示界面
- 调用 `apps/api` 提供的 `API v0` 接口
- 通过轮询方式读取任务状态与结果状态

### 2. `apps/api`

职责：

- 作为本地后端 HTTP 入口
- 使用 `FastAPI` 提供接口
- 使用 `Pydantic` 承担请求响应 DTO 与边界校验
- 调用 `packages/application/` 组织业务用例

### 3. `apps/worker`

职责：

- 承接异步执行、长文本任务与本机回归任务
- 复用 `packages/application/` 与 `PocketFlow` 组织多阶段执行
- 作为可选后台进程运行，不要求始终启动

### 4. `packages/application`

职责：

- 组织创建任务、读取任务、读取结果与执行评分主线等用例
- 协调 Prompt Runtime、Provider Adapter 与 Schema 校验

### 5. `packages/provider-adapters`

职责：

- 收敛 `DeepSeek API` 调用细节
- 统一异常、超时、重试与执行元信息

### 6. 外部模型 Provider

当前 `Phase 1` 默认且唯一正式接入的是 `DeepSeek API`。

说明：

- 本地部署不意味着模型在本机执行
- 本地后端仍会通过 Provider Adapter 调用外部模型 API

## 典型调用链

### 场景一：用户发起一次评测

```text
用户
-> apps/web
-> apps/api
-> packages/application
-> packages/prompt-runtime
-> packages/provider-adapters
-> DeepSeek API
-> packages/schemas 校验
-> apps/api 返回任务对象 / 结果语义
```

### 场景二：本机执行异步或回归任务

```text
开发者或后台触发
-> apps/worker
-> packages/application
-> packages/prompt-runtime
-> packages/provider-adapters
-> DeepSeek API
-> packages/schemas 校验
-> 本机报告或任务状态更新
```

## 启动假设

本地开发与使用时，通常按以下方式组织：

1. 安装前后端依赖
2. 配置 `DeepSeek API` 相关环境变量
3. 启动 `apps/api`
4. 启动 `apps/web`
5. 如需异步执行或回归，再启动 `apps/worker`

说明：

- 具体启动命令应以各应用目录文档为准
- Python 相关命令统一使用 `uv run`

## 文档约束

- 本地拓扑只说明运行关系，不替代 API 契约
- 任务状态、结果状态与错误语义仍以 `apps/api/contracts/` 为准
- 后端技术路线仍以 `docs/architecture/backend-technical-route.md` 为准

## 与现有文档的关系

- 后端技术路线见 `docs/architecture/backend-technical-route.md`
- 系统总览见 `docs/architecture/system-overview.md`
- API 契约见 `apps/api/contracts/api-v0-overview.md`
- 应用层边界见 `docs/architecture/application-layer-boundaries.md`
