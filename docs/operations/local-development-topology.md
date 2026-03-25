# 本地开发与部署拓扑

## 部署定位

`Phase 1` 固定为开源、本地部署、本机联调、单用户。

## 组件拓扑

```text
Browser
-> apps/web
-> apps/api
-> SQLite
-> DeepSeek API

apps/worker
-> evals
-> SQLite / reports / baselines
```

## 角色分工

### `apps/web`

- 创建任务
- 轮询状态
- 查看结果和历史

### `apps/api`

- 接收用户请求
- 写入 `SQLite`
- 进程内执行用户任务
- 返回任务/结果/history

### `apps/worker`

- 只运行 `batch`
- 只运行 `eval`
- 写出 report/baseline

### `SQLite`

- `Phase 1` 唯一本地状态存储

## 启动假设

1. 安装 API、worker、web 依赖
2. 配置环境变量
3. 启动 API
4. 启动 web
5. 需要回归时再启动 worker

## 当前不采用

- 消息队列前置依赖
- 分布式 worker 集群
- 公网负载均衡
- 多租户部署拓扑
