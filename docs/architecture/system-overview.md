# 系统总览

## 系统目标

构建一个面向网络小说投稿评估场景的智能打分系统，核心能力是 `LLM as Judge`。系统需要在保持可解释性、结构稳定性与正式契约一致性的前提下，对作者提交的“前几章节正文 + 后续大纲规划”生成结构化评分结果。

## 当前实现基线

- 前端：`Next.js (App Router) + React + TypeScript`
- 后端：`Python 3.13 + uv + FastAPI + Pydantic`
- LLM Provider：`DeepSeek API`
- LLM 编排：`PocketFlow`
- 部署定位：开源项目，本地部署、本机启动、前后端协同运行

## 系统组成

### 1. 用户交互层

由 `apps/web` 承载，用于：

- 输入或上传前几章节正文
- 输入或上传后续大纲规划
- 发起联合评测任务
- 查看评分结果、分析结果与可视化信息

### 2. 服务接口层

由 `apps/api` 承载，用于：

- 通过 `FastAPI` 提供 HTTP 接口入口
- 使用 `Pydantic` 表达请求响应 DTO 与运行时校验
- 接收联合投稿包评分请求
- 校验输入边界
- 触发评分流程
- 返回结构化结果
- 提供任务状态与错误信息

### 3. 异步执行层

由 `apps/worker` 承载，用于：

- 复用 `PocketFlow` 组织联合输入任务与异步执行
- 长文本任务处理
- 批量评测
- 回归任务执行
- 报告生成

### 4. 核心领域层

由 `packages/domain` 与 `packages/application` 承载，用于：

- 表达联合投稿包与评分对象
- 表达 `rubric` 规则、骨架层与结果结构
- 编排 Prompt、Provider、Schema 与输出结果
- 承接新 `8` 轴主评价层、旧四维骨架层与聚合逻辑
- 保持业务语义不被 Web 框架或编排框架侵占

### 5. Provider 适配层

由 `packages/provider-adapters` 承载，用于：

- 收敛 `DeepSeek API` 调用细节
- 隐藏 Provider SDK、鉴权与错误格式差异
- 向应用层与 `PocketFlow` 暴露稳定调用接口
- 为未来扩展其他 Provider 保留抽象边界

### 6. Prompt 治理层

由 `prompts/` 与 `packages/prompt-runtime` 承载，用于：

- 管理正式 Prompt 资产
- 实现 Prompt 的加载、渲染、版本控制与约束检查
- 为 `screening`、`rubric`、`aggregation` 三类评分 Prompt 提供治理边界

### 7. 评测回归层

由 `evals/` 承载，用于：

- 维护联合输入评测样本
- 执行回归验证
- 追踪 Prompt、Schema 或 Provider / Model 调整后的质量变化
- 复用正式评分主线做本机回归

## 正式评分主线

当前正式评分主线固定为：

1. 输入预检查
2. `LLM rubric` 分点评价
3. 轻量一致性整理
4. 新模型聚合输出
5. 正式结果投影

说明：

- 该主线是当前仓库唯一正式评分路径
- 正式输入对象以 `chapters + outline` 联合模型为中心
- 对外正式结果结构保持稳定
- 对内评分机制按阶段契约演进
- 该主线通常由 `PocketFlow` 组织执行，但阶段语义仍由架构与契约文档定义

## 正式评分结构

系统内部正式评分结构采用三层：

1. 新 `8` 轴主评价层
2. 旧四维骨架层
3. 对外四分投影层

新 `8` 轴主评价层固定为：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

旧四维骨架层固定为：

- `marketAttraction`
- `narrativeExecution`
- `characterMomentum`
- `noveltyUtility`

对外继续保留稳定四分字段：

- `signingProbability`
- `commercialValue`
- `writingQuality`
- `innovationScore`

此外，`fatalRisk` 作为跨层约束维度保留。

## 部署与运行假设

- 作为开源项目发布
- 用户在本地安装依赖并配置 `DeepSeek API` 所需环境变量
- 用户本机启动 `apps/web` 与 `apps/api`
- 如需要异步执行或回归任务，可在本机启动 `apps/worker`
- 当前不以内置公网高并发 SaaS 为前提

## 核心约束

- Prompt 必须只在后端治理
- 输出必须是严格 JSON
- `packages/schemas/` 是正式结构真源
- `Pydantic` 只负责边界表达与运行时校验，不替代正式 Schema
- `DeepSeek API` 是 `Phase 1` 默认且唯一正式接入 Provider
- `PocketFlow` 负责编排，不负责定义业务规则真源
- 研究产物不得直接演变为正式业务实现
- 结构边界优先于技术选型
- 对外正式结果结构应保持稳定，内部评分机制可分阶段演进
