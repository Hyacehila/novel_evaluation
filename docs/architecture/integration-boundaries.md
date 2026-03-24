# 集成边界说明

## 文档目的

本文档从集成视角说明小说智能打分系统中 API、Worker、Application、Prompt Runtime、Provider Adapter、Schemas、Evals 之间的交互边界，用于辅助跨模块协作与后续实现对齐。

本文档回答的问题是：

- 各模块在集成时如何交互
- 数据流与控制流如何穿过各模块
- 失败应在哪一层被识别和传播
- 哪些模块是稳定边界，哪些模块可替换

本文档不负责：

- 替代应用层职责真源文档
- 替代 API 契约真源文档
- 替代 Prompt 或 Schema 版本治理文档

## 核心集成面

当前系统的主要集成面包括：

- 前端与 API
- API 与 Application
- Application 与 Prompt Runtime
- Application 与 Provider Adapter
- Application 与 Schemas
- Worker 与 Application
- Evals 与 Application / Schemas / Prompt 资产

## 集成原则

- 所有外部请求统一通过 API 边界进入
- `apps/api` 以 `FastAPI + Pydantic` 承接 HTTP 入口与边界校验
- 所有核心业务编排统一通过 Application 层组织
- 多阶段评分执行优先以受控 `PocketFlow` 编排
- 所有正式结构定义统一回到 Schemas
- 所有 Prompt 资产统一通过 Prompt Runtime 接入
- 所有 Provider 细节统一通过 Adapter 封装，`Phase 1` 默认正式接入 `DeepSeek API`
- 所有回归验证统一通过 Evals 观测，不直接定义业务语义

## 数据流与控制流

## 场景一：在线创建并执行评测任务

```text
Frontend
-> API
-> Application
-> Prompt Runtime
-> Provider Adapter
-> Schemas 校验
-> Application 汇总任务结果
-> API 返回任务对象
-> 结果对象通过独立结果读取接口获取
```

### 数据流说明

- 前端提交业务输入
- API 解析请求并转为应用层可处理的输入
- Application 调用 Prompt Runtime 选择 Prompt
- Application 以受控 `PocketFlow` 编排组织多阶段执行
- Application 调用 Provider Adapter 完成模型执行，默认通过 `DeepSeek API` 适配能力落地
- 输出结果回到 Schemas 做正式校验
- Application 决定任务状态、结果状态与错误语义
- API 将其包装为统一响应

## 场景二：异步任务执行

```text
Worker
-> Application
-> Prompt Runtime
-> Provider Adapter
-> Schemas 校验
-> Application 更新任务结论
```

### 控制流说明

- Worker 是后台执行入口，而不是业务真源
- Worker 不应拥有独立的任务状态语义定义权
- Worker 应复用 Application 中的用例编排与状态约束
- Worker 在本地部署场景下可作为可选进程运行，不要求先构建复杂分布式调度系统

## 场景三：评测回归执行

```text
Evals Runner
-> Prompt 资产 / Prompt Runtime
-> Application 或受控执行入口
-> Provider Adapter
-> Schemas
-> Reports / Baselines
```

### 说明

- Evals 负责验证，不反向定义生产语义
- Evals 可以引用 Application 能力，但不应把测试路径变成正式业务真源

## 模块间输入输出边界

## Frontend <-> API

### 输入

- 文本输入
- 文件上传语义
- 输入类型与基础业务参数

### 输出

- 任务对象
- 结果对象
- 首页摘要对象
- 历史记录对象
- 统一错误对象

### 约束

- 前端不接收未经校验的模型原始输出
- API 不返回伪结构结果

## API <-> Application

### 输入

- 已通过边界校验的请求对象

### 输出

- 任务用例结果
- 结果读取结果
- 错误分类结果

### 约束

- API 不直接承担业务编排
- Application 不依赖 HTTP 协议细节

## Application <-> Prompt Runtime

### 输入

- 当前任务上下文
- 目标阶段或目标用例语义
- 所需版本信息

### 输出

- 可执行 Prompt 内容与关联元信息

### 约束

- Application 不直接长期内嵌正式 Prompt 正文
- Prompt Runtime 不决定业务成败语义

## Application <-> Provider Adapter

### 输入

- 已渲染 Prompt
- 执行参数
- 目标 Provider / Model 选择信息

### 输出

- 模型调用结果
- 统一化异常
- 必要执行元信息

### 约束

- Provider Adapter 不决定最终业务结果结构是否合法
- 业务合法性由 Application + Schemas 共同约束

## Application <-> Schemas

### 输入

- 待校验请求对象
- 待校验正式结果对象
- 后续中间阶段对象

### 输出

- 合法 / 非法结构判定
- 校验失败语义

### 约束

- Schemas 不负责路由设计
- Application 不应绕过正式结构真源

## Worker <-> Application

### 输入

- 后台任务触发上下文

### 输出

- 任务推进结果
- 任务状态变更

### 约束

- Worker 不自定义任务状态机
- Worker 不成为第二套业务入口真源

## Evals <-> Production Assets

### 输入

- 样本
- Prompt 版本
- Schema 版本
- Provider / Model 选择

### 输出

- 比较结果
- 基线结果
- 失败分类

### 约束

- Evals 引用正式资产，但不替代正式资产的治理权

## 失败传播规则

### 边界输入失败

- 在 API 层识别
- Application 不负责纠正非法边界输入

### Prompt 选择失败

- 在 Application / Prompt Runtime 边界识别
- 应进入统一错误语义，不向前端泄露内部实现细节

### Provider 执行失败

- 在 Provider Adapter 层归一化
- 由 Application 决定任务状态与错误码

### 结构校验失败

- 由 Schemas 判定
- 由 Application 决定是进入 `failed` 还是 `blocked` 等业务语义路径

## 可替换组件与稳定组件

### 稳定组件

以下组件应尽量保持稳定：

- API 资源语义
- 任务状态机
- 正式结果结构真源位置
- Prompt 生命周期规则
- Schema 治理规则

### 可替换组件

以下组件允许受控替换：

- 具体 Provider
- 具体 Model
- Prompt 正文版本
- Worker 执行方式
- Evals Runner 的内部执行方式

说明：

- 可替换不等于可绕过治理
- 替换后仍需遵守对应文档约束

## 典型协作场景

### 场景一：前端联调 API

关注文档：

- `apps/api/contracts/api-v0-overview.md`
- `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- `docs/contracts/frontend-minimal-api-assumptions.md`
- `docs/contracts/frontend-api-consumption-and-query-strategy.md`

### 场景二：后端实现基线评分链路

关注文档：

- `docs/planning/mvp-phase-1-scope.md`
- `docs/architecture/application-layer-boundaries.md`
- `docs/architecture/scoring-pipeline.md`
- `docs/contracts/schema-versioning-policy.md`
- `docs/prompting/prompt-lifecycle.md`

### 场景三：回归 Prompt 或 Schema 变更

关注文档：

- `docs/prompting/prompt-lifecycle.md`
- `docs/contracts/schema-versioning-policy.md`
- `evals/README.md`

## 完成标准

满足以下条件时，可认为集成边界已足够清晰：

- 跨模块协作时，团队知道调用链从哪一层进入、在哪一层结束
- 失败传播责任归属清晰
- 新增 Provider、Worker 或 Evals Runner 时不会抢占业务定义权
- 前后端联调、后端实现、回归评测三类协作场景都能找到对应边界说明

## 与现有文档的关系

- 后端目录职责见 `docs/architecture/application-layer-boundaries.md`
- API 资源语义见 `apps/api/contracts/api-v0-overview.md`
- 状态与错误语义见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- Prompt 治理见 `docs/prompting/prompt-lifecycle.md`
- Schema 治理见 `docs/contracts/schema-versioning-policy.md`
- 评测回归见 `evals/README.md`
