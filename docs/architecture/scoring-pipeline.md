# 评分流水线

本文档定义小说智能打分系统的正式评分流程。

当前仓库只保留一条正式主线：

- **正式评分流程**：输入预检查 → `LLM rubric` 分点评价 → 轻量一致性整理 → 新模型聚合输出 → 正式结果投影

相关专题文档：

- `docs/architecture/layered-rubric-evaluation-architecture.md`
- `docs/contracts/rubric-stage-contracts.md`
- `docs/decisions/ADR-004-layered-rubric-evaluation.md`
- `docs/architecture/backend-technical-route.md`
- `docs/architecture/provider-abstraction.md`

## 正式评分流程

1. 接收用户提交的联合输入
2. 校验输入结构与基本边界
3. 构建评分任务对象
4. 选择 `rubric` 版本、Prompt 版本与执行配置
5. 执行输入预检查与可评性判断
6. 执行新 `8` 轴 `LLM rubric` 分点评价
7. 执行轻量一致性整理
8. 由新模型聚合到旧四维骨架层并生成最终结果草案
9. 生成正式结果对象并校验严格 JSON 输出
10. 返回正式结构化结果
11. 记录日志、阶段元数据与评测信息

## 技术承接关系

- `apps/api` 使用 `FastAPI` 提供接口入口，并以 `Pydantic` 承担请求响应 DTO 与边界校验
- `packages/application` 负责组织创建任务、读取任务、执行评分主线等用例
- `packages/application.scoring_pipeline` 负责组织输入预检查、分点评价、一致性整理与聚合输出等多阶段执行链
- `packages/provider-adapters` 负责把正式模型调用收敛到统一接口，`Phase 1` 默认正式接入 `DeepSeek API`
- `packages/schemas/` 是正式结果结构真源，运行时校验不得重新定义结构语义

## 每一步的职责

### 输入接收

- 由 `FastAPI` 路由接收边界输入
- 正式输入以联合投稿包为中心
- 不在边界层处理深层评分业务规则

### 输入校验

- 通过 `Pydantic` 校验请求结构与基础边界
- 校验 `chapters` 与 `outline` 字段结构是否合法
- 校验是否至少存在一个正式输入源
- 校验用户配置结构是否合法

### 任务构建

- 为后续执行统一上下文
- 记录 Prompt、Schema、Provider 的版本信息
- 记录联合输入组成与评估模式
- 为同步接口与异步 worker 保持一致任务语义

### Prompt 与 Rubric 选择

- 根据评分任务选择合适 Prompt
- 根据联合输入组成、轻量标签与版本信息选择对应 `rubric`
- 当前正式模型调用默认面向 `DeepSeek API`
- 不允许前端传入正式评分 Prompt 正文
- Prompt 与 `rubric` 的版本关系应可追踪

### 输入预检查

- 判断联合输入是否可评
- 识别输入组成是 `chapters_outline`、`chapters_only` 还是 `outline_only`
- 判断输入充分性与是否需要降级评估
- 识别明显非小说文本、信息不足或结构失真文本
- 为后续分点评价提供上下文

### 新 `8` 轴 `LLM rubric` 分点评价

- 按新 `8` 轴输出结构化评价项
- 每项同时给出分档、理由、文本依据和风险标签
- 证据需标明来自 `chapters`、`outline` 或 `cross_input`
- 产出聚合模型可直接消费的中间结果

### 轻量一致性整理

- 检查缺项、冲突、重复处罚和无依据判断
- 重点检查正文与大纲之间是否存在承诺冲突
- 只负责整理与提示，不负责重新生成完整结果
- 为聚合模型提供更干净的输入对象

### 聚合输出

- 读取预检查结果、分点评价结果和一致性整理结果
- 通过 `ScoringPipeline` 组织聚合阶段执行，但不让编排层重定义业务字段
- 先汇总到旧四维骨架层，再投影为顶层分数、强弱项、平台建议、市场判断和编辑结论
- 保持顶层字段之间的逻辑关系稳定

### JSON 校验与结果投影

- 将输出视为必须满足的结构契约
- 对外正式结果应以 `packages/schemas/` 为真源进行校验
- `Pydantic` 可以承担 API 边界与运行时对象校验，但不替代 Schema 真源
- 非法输出进入失败路径
- 对外正式结果与对内阶段契约都应是严格 JSON
- 中间阶段契约只作为后端内部治理对象，不直接暴露为前端正式结果

### 失败处理

- 可以记录错误
- 可以触发有限重试策略
- Provider 失败应在适配层收敛为统一错误语义
- 不得返回无法解析的伪结构化结果
- 应区分联合输入不可评、单侧输入不足、分点评价失败、一致性冲突、聚合失败、Provider 失败等不同失败语义

## 设计目标

- 流水线标准化
- 错误路径清晰
- 契约优先
- 本地部署可运行
- 支持未来回归评测与版本治理
