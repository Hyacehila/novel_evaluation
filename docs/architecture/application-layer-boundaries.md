# 应用层边界说明

## 文档目的

本文档用于明确小说智能打分系统在 `Phase 1` 开发中的后端分层边界，回答以下问题：

- 各目录分别负责什么
- 各目录不应负责什么
- 依赖方向应如何保持稳定
- 一条标准请求应如何穿过这些层
- 哪些常见实现方式属于越界

本文档不负责：

- 定义具体 API 路由细节
- 定义正式 Schema 字段本体
- 定义 Prompt 正文内容
- 定义数据库表结构

## 适用范围

本文档覆盖以下目录：

- `apps/api/`
- `apps/worker/`
- `packages/application/`
- `packages/domain/`
- `packages/provider-adapters/`
- `packages/prompt-runtime/`
- `packages/schemas/`
- `packages/shared/`
- `evals/`

## 核心分层原则

### 1. 接口层不承载核心业务编排

`apps/api/` 的职责是：

- 以 `FastAPI` 提供 HTTP 接口入口
- 以 `Pydantic` 承担系统边界校验与 DTO 表达
- 接收请求
- 调用应用层用例
- 返回统一响应

`apps/api/` 不应直接承载：

- Prompt 选择规则本体
- Provider 细节适配
- 输出结构定义
- 长流程业务编排

### 2. 应用层负责用例编排

`packages/application/` 是 `Phase 1` 最核心的后端业务编排层，用于：

- 组织评分任务流程
- 组合 Prompt Runtime、Provider Adapter、Schema 校验能力
- 以受控方式复用 `PocketFlow` 组织多阶段评分主线
- 统一任务状态推进
- 统一失败路径进入方式

### 3. 领域层负责表达稳定业务概念

`packages/domain/` 负责：

- 领域对象
- 领域术语
- 评分对象语义
- 任务与结果的业务概念边界

`packages/domain/` 不应直接依赖：

- Web 框架
- 具体 Provider SDK
- 前端 View Model

### 4. Schema 是正式结构真源

`packages/schemas/` 是正式结构定义的唯一真源，用于：

- 请求对象结构
- 对外结果结构
- 中间阶段结构
- 评测结构

说明：

- 文档可以解释结构含义
- 但正式结构定义不能散落在 API 路由、Prompt 文件或前端适配层中

### 5. Prompt Runtime 与 Prompt 资产分离

- `prompts/` 存放正式 Prompt 资产
- `packages/prompt-runtime/` 负责加载、选择、渲染、版本约束与运行时治理

这意味着：

- Prompt 正文不应硬编码进 API 层
- Prompt 选择规则不应由前端承担

### 6. Provider Adapter 向上提供统一执行接口

`packages/provider-adapters/` 负责：

- 统一模型调用接口
- 统一异常归类
- 统一超时与重试策略约束

它不应负责：

- 定义业务评分字段
- 解释业务语义
- 决定页面展示逻辑

## 各层职责边界

## 1. `apps/api/`

### 负责什么

- HTTP 路由与请求入口
- 请求解析与边界输入校验
- 调用应用层用例
- 返回统一响应 envelope
- 映射 HTTP 状态码与错误对象

### 不负责什么

- 直接拼接 Prompt 正文
- 直接调用具体供应商 SDK
- 自行定义正式结果结构
- 在路由内部写完整评分业务流程

### 典型产物

- 路由处理器
- 请求 DTO 适配
- 响应包装器
- 错误响应映射

## 2. `apps/worker/`

### 负责什么

- 异步任务执行入口
- 回归任务执行入口
- 批量任务触发
- 与应用层用例对接的后台执行接口

### 不负责什么

- 定义正式业务契约
- 直接承接前端展示逻辑
- 直接定义 Prompt 正文

### `Phase 1` 说明

- `apps/worker/` 在 `Phase 1` 中可以先保持边界明确、实现轻量
- 不要求先做复杂调度系统

## 3. `packages/application/`

### 负责什么

- 任务创建用例
- 任务读取用例
- 结果读取用例
- 基线评分编排用例
- 任务状态流转协调
- 结果校验与失败路径协调

### 不负责什么

- HTTP 协议细节
- 页面消费对象
- 具体供应商 SDK 细节
- Prompt 原文存储

### 建议组织方式

优先按用例组织，而不是按技术类型组织，例如：

- 创建任务用例
- 运行评分用例
- 读取任务详情用例
- 读取结果详情用例
- 首页摘要聚合用例
- 历史记录查询用例

## 4. `packages/domain/`

### 负责什么

- `Manuscript`
- `EvaluationTask`
- `EvaluationResult`
- 评分维度语义
- 任务状态的业务含义
- 错误语义的业务分类

### 不负责什么

- HTTP 状态码
- Query Key
- SDK 请求结构
- UI 展示字段命名

## 5. `packages/provider-adapters/`

### 负责什么

- 模型供应商调用抽象
- 请求与响应适配
- 超时、重试、异常归一化
- 上报 Provider 执行元数据
- 收敛 `Phase 1` 默认正式 Provider `DeepSeek API` 的调用细节

### 不负责什么

- 决定业务是否成功
- 决定任务状态是否可对外展示
- 直接输出最终页面结果结构

## 6. `packages/prompt-runtime/`

### 负责什么

- 按规则选择 Prompt 资产
- 渲染 Prompt 所需上下文
- 管理 Prompt 版本元信息
- 为应用层提供可调用的 Prompt Runtime 接口

### 不负责什么

- 存放 Prompt 正文真源
- 绕过版本治理直接使用临时 Prompt
- 在运行时向前端暴露 Prompt 内部细节

## 7. `packages/schemas/`

### 负责什么

- 定义正式请求结构
- 定义正式响应结构
- 定义必要中间结构
- 定义 Evals 结构

### 不负责什么

- 定义路由 URL
- 定义页面模型
- 定义 Prompt 原文

## 8. `packages/shared/`

### 负责什么

- 配置
- 日志
- 通用错误基类
- 通用工具
- 与具体业务无关的基础设施支持

### 不负责什么

- 沉积具体评分业务逻辑
- 成为“什么都能放”的杂物层

## 9. `evals/`

### 负责什么

- 样本组织
- 基线说明
- 报告产物组织
- 回归执行入口说明

### 不负责什么

- 成为正式线上业务实现目录
- 反向定义 API 契约

## 依赖方向

推荐依赖方向如下：

```text
apps/api -> packages/application -> packages/domain
                                 -> packages/prompt-runtime
                                 -> packages/provider-adapters
                                 -> packages/schemas
                                 -> packages/shared

apps/worker -> packages/application -> 同上

evals -> packages/schemas / packages/application（受控使用）
```

约束：

- `packages/domain/` 不反向依赖 `apps/api/`
- `packages/provider-adapters/` 不依赖前端文档模型
- `apps/api/` 不绕过 `packages/application/` 直接组织完整评分流程

## 标准调用链

## 场景一：创建评测任务

```text
HTTP 请求
-> apps/api 路由
-> 请求校验与 DTO 适配
-> packages/application 创建任务用例
-> packages/domain 构建任务对象
-> 持久化/任务登记（后续实现）
-> apps/api 响应封装
```

## 场景二：执行基线评分

```text
任务触发
-> packages/application 基线评分用例
-> 受控 `PocketFlow` 编排节点
-> packages/prompt-runtime 选择并渲染 Prompt
-> packages/provider-adapters 执行模型调用
-> packages/schemas 校验输出结构
-> packages/application 判定成功/失败与状态推进
-> 结果返回或持久化（后续实现）
```

## 场景三：读取正式结果

```text
HTTP 请求
-> apps/api 路由
-> packages/application 结果读取用例
-> packages/schemas 对结果结构进行正式约束
-> apps/api 封装响应
```

## 典型越界反例

### 反例 1：在路由里直接拼 Prompt

错误原因：

- 破坏 Prompt 治理边界
- 导致版本追踪失效
- 让接口层承担业务策略

### 反例 2：在 Provider Adapter 里定义业务结果字段

错误原因：

- Provider 层应做适配，不应拥有业务结构解释权
- 会导致更换 Provider 时业务语义漂移

### 反例 3：在前端假契约中反向定义正式 Schema

错误原因：

- 前端文档可以提供假契约
- 但正式结构真源只能在 `packages/schemas/`

### 反例 4：把 `packages/shared/` 当作业务实现主目录

错误原因：

- 会破坏目录职责清晰度
- 导致业务能力无法按边界沉淀

## 目录级落位建议

### `apps/api/`

建议优先放置：

- 路由入口
- 请求/响应适配层
- API 级错误映射

### `packages/application/`

建议优先放置：

- 基线评分用例
- 任务查询用例
- 结果查询用例
- 首页聚合用例
- 历史查询用例

### `packages/domain/`

建议优先放置：

- 任务对象
- 结果对象
- 输入对象
- 业务状态语义

### `packages/schemas/`

建议优先放置：

- API 请求与响应正式结构
- 正式结果结构
- 后续阶段中间结构

## 完成标准

当满足以下条件时，可认为应用层边界已明确：

- 团队可以按目录分配后端开发任务
- API 层、应用层、领域层、Prompt Runtime、Provider Adapter 的职责无明显重叠
- 任何一个功能点都能判断其应落在哪一层
- 新增代码时可以据此识别越界实现

## 与现有文档的关系

- 系统总览见 `docs/architecture/system-overview.md`
- 领域对象见 `docs/architecture/domain-model.md`
- Provider 边界见 `docs/architecture/provider-abstraction.md`
- 评分流程见 `docs/architecture/scoring-pipeline.md`
- 正式结构语义见 `docs/contracts/json-contracts.md`
