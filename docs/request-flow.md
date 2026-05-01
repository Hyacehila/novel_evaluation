# 后端小说评测主链请求说明

这份文档只讲一件事：一次 `POST /api/tasks` 提交后，后端实际会按什么顺序工作，分别发出哪些模型请求，每次请求使用哪份 Prompt，想解决什么评价问题，以及后端最后如何采信、修正、阻断或落库。

## 范围

- 只覆盖单次评测任务主链，不展开 `dashboard`、`history` 等非主链接口。
- 当前正式 provider 口径以 `provider-deepseek + deepseek-v4-pro` 为准。
- 当前正式主链固定为：
  `input_screening -> type_classification -> rubric_evaluation -> type_lens_evaluation -> consistency_check -> aggregation -> final_projection`
- `consistency_check` 与 `final_projection` 是规则/投影阶段，不发模型请求。

## 先看结论

在 `screening` 未阻断、`consistency` 未阻断、且没有失败重试的正常成功路径上，后端会对 DeepSeek 发出 `7` 次模型请求：

| 顺序 | 阶段 | 是否模型请求 | Prompt ID | 说明 |
| --- | --- | --- | --- | --- |
| 1 | `input_screening` | 是 | `screening-default` 或 `screening-degraded` | 判断材料能否进入正式评分 |
| 2 | `type_classification` | 是 | `type-classification-default` 或 `type-classification-degraded` | 输出 Top-3 题材候选 |
| 3 | `rubric_evaluation` 切片 1 | 是 | `rubric-default` 或 `rubric-degraded` | 评 3 个通用轴 |
| 4 | `rubric_evaluation` 切片 2 | 是 | `rubric-default` 或 `rubric-degraded` | 再评 3 个通用轴 |
| 5 | `rubric_evaluation` 切片 3 | 是 | `rubric-default` 或 `rubric-degraded` | 最后评 2 个通用轴 |
| 6 | `type_lens_evaluation` | 是 | `type-lens-default` 或 `type-lens-degraded` | 只评最终类型对应的 4 个 lens |
| 7 | `consistency_check` | 否 | 无 | 规则检查，可能阻断 |
| 8 | `aggregation` | 是 | `aggregation-default` 或 `aggregation-degraded` | 收束成总体判断草稿 |
| 9 | `final_projection` | 否 | 无 | 投影为前端正式结果 |

当前实现还有两层重试，因此“真实外部请求次数”可能大于 `7`：

- DeepSeek adapter 对 `json_object` 请求最多会因为空内容或 JSON 截断再试 `1` 次。
- `type_classification`、每个 `rubric` 切片、`type_lens`、`aggregation` 在 schema 校验失败时，还会整阶段再试 `1` 次。

按当前代码推导，正常成功路径的名义请求数是 `7`，而在极端 JSON/Schema 重试路径下，外部模型请求数最多可达 `26`。这个上限来自代码推导，不是额外配置项。

## 入口边界：`POST /api/tasks`

入口在 [`apps/api/src/api/routes.py`](../apps/api/src/api/routes.py) 的 `create_task`。

### 1. 请求先被 API 路由接收

`POST /api/tasks` 先做两件事：

1. 调 `provider_runtime.get_status()`，如果 `canAnalyze=false`，直接返回 `409`，不会创建任务。
2. 解析提交内容，生成 `JointSubmissionRequest`。

### 2. 提交内容支持两种形态

- `application/json`
  - 通过 `_parse_json_submission`
  - 直接反序列化成 [`JointSubmissionRequest`](../packages/schemas/input/joint_submission.py)
- `multipart/form-data`
  - 通过 `_parse_multipart_submission`
  - 读取 `chaptersFile` / `outlineFile`
  - 允许 `TXT / MD / DOCX`
  - 转成同一个 `JointSubmissionRequest`

底层真源在 [`packages/schemas/input/manuscript.py`](../packages/schemas/input/manuscript.py)：

- `title`
- `chapters[]`
- `outline`
- `sourceType`

并由 schema 自动推导：

- `hasChapters`
- `hasOutline`
- `inputComposition`
  - `chapters_outline`
  - `chapters_only`
  - `outline_only`

### 3. 任务创建和异步执行是分开的

API 并不会在 `POST /api/tasks` 的同步请求里跑完整个评测。

它会先：

1. 调 [`EvaluationService.create_task`](../packages/application/services/evaluation_service.py)
2. 创建一条 `queued + not_available` 的任务记录
3. 通过 `BackgroundTasks` 调度 `EvaluationService.execute_task(taskId, submission)`
4. 立即返回 `201`

这意味着：

- `POST /api/tasks` 返回时，模型请求通常还没开始。
- 前端随后应轮询：
  - `GET /api/tasks/{taskId}`
  - `GET /api/tasks/{taskId}/result`

### 4. 创建任务时不会发模型请求

`create_task` 阶段只会用 [`_build_input_screening`](../packages/application/services/evaluation_service.py) 预填一份任务元数据：

- 初始 `evaluationMode`
  - `chapters_outline -> full`
  - 其他 -> `degraded`
- 初始 `schemaVersion / promptVersion / rubricVersion / providerId / modelId`

这一步只是任务元数据初始化，不会调用 DeepSeek。

## 所有模型请求的统一拼接方式

真正发给模型的入口统一在 [`packages/application/scoring_pipeline/provider_support.py`](../packages/application/scoring_pipeline/provider_support.py) 的 `execute_provider_stage`。

每个阶段都会被拼成统一的 provider request：

```json
{
  "taskId": "...",
  "stage": "...",
  "promptId": "...",
  "promptVersion": "v1",
  "schemaVersion": "1.0.0",
  "rubricVersion": "rubric-v1",
  "providerId": "provider-deepseek",
  "modelId": "deepseek-v4-pro",
  "requestId": "...",
  "messages": [
    { "role": "system", "content": "Markdown Prompt 正文" },
    { "role": "user", "content": "JSON 字符串化后的 user_payload" }
  ],
  "inputComposition": "...",
  "evaluationMode": "...",
  "timeoutMs": "...",
  "maxTokens": "...",
  "responseFormat": { "type": "json_object" }
}
```

当前 DeepSeek adapter 在 [`packages/provider-adapters/src/provider_adapters/deepseek.py`](../packages/provider-adapters/src/provider_adapters/deepseek.py) 里把它映射成：

```json
{
  "model": "deepseek-v4-pro",
  "messages": [
    { "role": "system", "content": "Prompt Markdown" },
    { "role": "user", "content": "{\"taskId\":\"...\", ...}" }
  ],
  "max_tokens": "...",
  "response_format": { "type": "json_object" },
  "extra_body": { "thinking": { "type": "enabled" } },
  "reasoning_effort": "high"
}
```

这里有两个关键点：

- `system` 消息始终是 `prompts/scoring/.../v1.md` 的完整 Markdown 正文。
- `user` 消息始终是后端代码构造的结构化 JSON，不是自然语言补充说明。
- DeepSeek V4 思考模式由 adapter 显式传入；如需降本或关闭思考，在 `.env` 修改对应 `NOVEL_EVAL_DEEPSEEK_*` 配置。

## Prompt 是如何选中的

Prompt 选择逻辑在 [`packages/prompt-runtime/src/prompt_runtime/runtime.py`](../packages/prompt-runtime/src/prompt_runtime/runtime.py)。

选择顺序固定为：

1. `stage`
2. `inputCompositionScope`
3. `evaluationModeScope`
4. `providerScope`
5. `modelScope`
6. `status` 优先 `active`，其次 `candidate`
7. `enabled=true`

当前正式主链的 registry 都绑定到：

- `providerScope: provider-deepseek`
- `modelScope: *`
- `promptVersion: v1`

因此实际只会在 `default` 和 `degraded` 两套 Prompt 之间切换：

- `chapters_outline + full` 走 `*-default`
- 其余 `degraded` 路线走 `*-degraded`

## 主链详解

### 1. `input_screening`

实现入口：

- 编排：[`ScoringPipeline.run_screening`](../packages/application/scoring_pipeline/orchestration.py)
- 执行器：[`execute_screening`](../packages/application/scoring_pipeline/screening_executor.py)

Prompt 选择：

- `chapters_outline + full` -> [`screening-default`](../prompts/scoring/screening/screening-default/v1.md)
- `* + degraded` -> [`screening-degraded`](../prompts/scoring/screening/screening-degraded/v1.md)

#### 这次请求要解决什么

`screening` 不是打分，它只回答：

- 这份材料到底是 `chapters_outline`、`chapters_only` 还是 `outline_only`
- 正文和大纲是否分别“足够支撑后续判断”
- 当前任务应该进入：
  - `full`
  - `degraded`
  - 直接阻断
- 是否需要输出 `segmentationPlan`

它明确不负责：

- 8 轴评分
- 类型判定
- 总体结论

#### 发给模型的 `user_payload`

```json
{
  "taskId": "...",
  "title": "...",
  "inputComposition": "chapters_outline | chapters_only | outline_only",
  "evaluationModeHint": "full | degraded",
  "chapters": ["第一章正文...", "第二章正文..."],
  "outline": "大纲正文或 null"
}
```

#### Prompt 要模型怎么评

Prompt 的核心要求是：

- 用“偏编辑签约视角的网络小说投稿评估”去做材料预检查
- 判断正文是否能支撑开篇吸引力、叙事起点、角色驱动、故事推进的初步判断
- 判断大纲是否能支撑主线、阶段目标、升级兑现方向、平台和商业判断的保守基础
- 严禁把“有字”直接等同于“可评”
- 严禁越权进入逐轴评分

`screening-default` 更强调双输入联合判断，只有正文和大纲都充分才允许 `full`。

`screening-degraded` 更强调单侧输入时的保守策略：

- `chapters_only` 只能较稳地判断开篇和局部叙事
- `outline_only` 只能较稳地判断题材方向和长线承诺
- 任何一侧不足都不能伪装成完整双输入结论

#### 期望输出字段

模型必须返回 `InputScreeningResult` 语义的 JSON，包括：

- `chaptersSufficiency`
- `outlineSufficiency`
- `evaluationMode`
- `rateable`
- `status`
- `rejectionReasons`
- `riskTags`
- `segmentationPlan`
- `confidence`
- `continueAllowed`

#### 后端如何采信和修正

后端不会盲信模型原样输出，而是先做归一化：

- 强制回填 `taskId`、`stage`、版本号、provider 信息
- 用真实提交内容覆盖：
  - `inputComposition`
  - `hasChapters`
  - `hasOutline`
- 规范化 `riskTags`、`rejectionReasons`、`confidence`
- 若模型没给或给错充分性，后端会按“是否存在该侧输入”兜底成：
  - `sufficient`
  - `missing`
- `evaluationMode` 会按规则重新推断：
  - 只有 `chapters_outline` 且两侧都 `sufficient` 才能是 `full`
  - 其他都回到 `degraded`

另外还有一个“快速阻断”规则：

- 当输入是 `chapters_outline`
- 最终被判到 `degraded`
- 命中 `nonNarrativeSubmission` 或 `insufficientMaterial`
- 正文不足
- 且 `confidence <= 0.4`

后端会强制把本阶段结果压成：

- `rateable=false`
- `status=unrateable`
- `continueAllowed=false`

#### 失败与阻断

- 本阶段没有 schema 重试；一旦输出不满足 schema，会直接失败。
- 若 `continueAllowed=false`，真正的阻断发生在下一步 `_ensure_screening_continue_allowed`：
  - 正文不足 -> `INSUFFICIENT_CHAPTERS_INPUT`
  - 大纲不足 -> `INSUFFICIENT_OUTLINE_INPUT`
  - 其他不可评 -> `JOINT_INPUT_UNRATEABLE`

### 2. `type_classification`

实现入口：

- 编排：[`ScoringPipeline.run_type_classification`](../packages/application/scoring_pipeline/orchestration.py)
- 执行器：[`execute_type_classification`](../packages/application/scoring_pipeline/type_classification_executor.py)

Prompt 选择：

- `chapters_outline + full` -> [`type-classification-default`](../prompts/scoring/type-classification/type-classification-default/v1.md)
- `* + degraded` -> [`type-classification-degraded`](../prompts/scoring/type-classification/type-classification-degraded/v1.md)

#### 这次请求要解决什么

这一步只做题材归类，不做整体好坏判断。

目标是：

- 输出 `Top-3` 类型候选
- 解释每个候选为什么成立
- 把后续 `type_lens` 所需的题材方向先稳定下来

它明确不负责：

- 最终是否采用 `top1`
- 最终是否回落到 `general_fallback`
- 8 轴评分

#### 发给模型的 `user_payload`

```json
{
  "taskId": "...",
  "title": "...",
  "inputComposition": "...",
  "evaluationMode": "...",
  "chapters": ["..."],
  "outline": "...",
  "screening": { "...": "screening 全量结果" },
  "novelTypeCatalog": { "...": "所有正式 NovelType 与其 4 个 lens 目录" },
  "decisionPolicy": {
    "minConfidence": 0.60,
    "minMargin": 0.12,
    "fallbackType": "general_fallback",
    "femaleGeneralIsTerminal": true
  }
}
```

#### Prompt 要模型怎么评

Prompt 要求模型：

- 只能从正式枚举里选类型：
  - `female_general`
  - `fantasy_upgrade`
  - `urban_reality`
  - `history_military`
  - `sci_fi_apocalypse`
  - `suspense_horror`
  - `game_derivative`
  - `general_fallback`
- 必须给出 `3` 个候选，按置信度排序
- 识别题材信号，但不替代最终阈值裁决
- `degraded` 模式下不能把单一信号过度外推成高置信窄类型

#### 期望输出字段

- `candidates`
  - `novelType`
  - `confidence`
  - `reason`
- `summary`

#### 后端如何采信和修正

这一步后端的采信强于 Prompt 本身：

- 会先规范化 `candidates`
- 去掉无效或重复类型
- 不足 `3` 个时，用后端兜底候选补满 Top-3
  - 置信度兜底序列是 `0.55 / 0.43 / 0.31`
- 若模型没给 `summary`，后端会自动生成总结

真正的最终类型选择规则在 [`type_support.py`](../packages/application/scoring_pipeline/type_support.py)：

- `top1.confidence >= 0.60`
- 且 `top1 - top2 >= 0.12`

同时满足时：

- 最终 `novelType = top1`
- `fallbackUsed = false`

否则：

- 最终 `novelType = general_fallback`
- `fallbackUsed = true`

随后 `EvaluationService.sync_task_with_type_classification` 会把这些信息回写到任务上：

- `novelType`
- `typeClassificationConfidence`
- `typeFallbackUsed`

#### 重试与失败

- 本阶段 schema 校验最多尝试 `2` 次。
- 若 JSON 能解析但 schema 始终不合法，会以 `STAGE_SCHEMA_INVALID` 失败。

### 3. `rubric_evaluation` 第 1 次请求

### 4. `rubric_evaluation` 第 2 次请求

### 5. `rubric_evaluation` 第 3 次请求

实现入口：

- 编排：[`execute_rubric`](../packages/application/scoring_pipeline/rubric_executor.py)
- 切片执行：`execute_rubric_slice`

Prompt 选择：

- `chapters_outline + full` -> [`rubric-default`](../prompts/scoring/rubric/rubric-default/v1.md)
- `* + degraded` -> [`rubric-degraded`](../prompts/scoring/rubric/rubric-degraded/v1.md)

#### 为什么这里是 3 次请求

8 个通用轴不会一次性全发给模型，而是按 `RUBRIC_SLICE_PLAN` 拆成 3 个切片：

1. 第 1 片：
   - `hookRetention`
   - `serialMomentum`
   - `characterDrive`
2. 第 2 片：
   - `narrativeControl`
   - `pacingPayoff`
   - `settingDifferentiation`
3. 第 3 片：
   - `platformFit`
   - `commercialPotential`

这样做的直接效果是：

- 正常成功路径里，`rubric` 一定是 `3` 次模型请求
- 每次请求只评 `requestedAxes`，不允许补写其他轴

#### 每次切片请求的 `user_payload`

```json
{
  "taskId": "...",
  "title": "...",
  "inputComposition": "...",
  "evaluationMode": "...",
  "requestedAxes": ["hookRetention", "..."],
  "chapters": ["..."],
  "outline": "...",
  "screening": { "...": "screening 全量结果" }
}
```

#### Prompt 要模型怎么评

`rubric` Prompt 的核心目标是：

- 只评当前 `requestedAxes`
- 为每个轴给出：
  - `scoreBand`
  - `reason`
  - `evidenceRefs`
  - `confidence`
  - `riskTags`
  - `blockingSignals`
  - `degradedByInput`
- 给出与这些轴一一对应的 `axisSummaries`
- 只在真的无法负责任判断时，把轴放进 `missingRequiredAxes`

`rubric-default` 假设双输入更完整：

- full 模式下通常不应缺轴
- `degradedByInput` 通常应是 `false`

`rubric-degraded` 更强调：

- 受材料缺口影响的轴要显式标注 `degradedByInput=true`
- `confidence` 要保守
- 必要时可把无法稳定判断的轴放进 `missingRequiredAxes`
- 不能虚构另一侧输入的证据

#### 后端如何采信和修正

后端会逐项归一化：

- `items` 只保留当前请求的 `requestedAxes`
- `scoreBand` 支持别名归一化到 `"0"` 到 `"4"`
- 为缺失或格式错误的 `evidenceRefs` 自动补保守证据占位
- 规范化 `riskTags`、`blockingSignals`
- 从 `reason` 和 `axisSummaries` 中补齐轴摘要

每个切片 schema 校验通过后，3 个切片会被合并成一份 `RubricEvaluationSet`：

- `items` 必须最终覆盖全部 `8` 轴
- `axisSummaries` 最终也必须覆盖全部 `8` 轴
- `missingRequiredAxes` 是合并后的缺轴结果
- `overallConfidence` 取 3 个切片中的最小值

#### 这一步真正想评价什么

8 个通用轴是这套系统的主体评分骨架：

- `hookRetention`：开篇钩子和读者留存抓手
- `serialMomentum`：连载推进惯性
- `characterDrive`：角色目标和行动驱动力
- `narrativeControl`：叙事组织与控制
- `pacingPayoff`：节奏与兑现
- `settingDifferentiation`：设定差异化
- `platformFit`：平台/圈层适配
- `commercialPotential`：商业潜力

也就是说，`rubric` 才是“通用评分主干”，但它依然不是最终结论，只是给后面的 `consistency`、`aggregation` 和 `projection` 提供结构化中间结果。

#### 重试与失败

- 每个切片 schema 校验最多尝试 `2` 次。
- 因为一共有 `3` 个切片，所以 `rubric` 是最容易放大整体请求次数的阶段。

### 6. `type_lens_evaluation`

实现入口：

- 编排：[`execute_type_lens`](../packages/application/scoring_pipeline/type_lens_executor.py)

Prompt 选择：

- `chapters_outline + full` -> [`type-lens-default`](../prompts/scoring/type-lens/type-lens-default/v1.md)
- `* + degraded` -> [`type-lens-degraded`](../prompts/scoring/type-lens/type-lens-degraded/v1.md)

#### 这次请求要解决什么

这一阶段不是重做类型分类，而是回答：

- 在“最终题材类型已经选定”的前提下
- 该类型最关键的 `4` 个专属 lens 表现如何

它是对通用 8 轴的补充，不是替代。

#### 发给模型的 `user_payload`

```json
{
  "taskId": "...",
  "title": "...",
  "inputComposition": "...",
  "evaluationMode": "...",
  "chapters": ["..."],
  "outline": "...",
  "screening": { "...": "screening 全量结果" },
  "typeClassification": { "...": "type classification 全量结果" },
  "selectedType": {
    "novelType": "...",
    "label": "...",
    "lenses": [
      { "lensId": "...", "label": "..." },
      { "lensId": "...", "label": "..." },
      { "lensId": "...", "label": "..." },
      { "lensId": "...", "label": "..." }
    ]
  }
}
```

#### Prompt 要模型怎么评

Prompt 要求模型：

- 只评 payload 里给定的 `4` 个 lens
- 不重做题材判断
- 不替代 8 轴 `rubric`
- 结论必须基于：
  - 正文
  - 大纲
  - screening
  - 已确定的类型目录

`degraded` 版本额外强调：

- 输入不完整时仍然必须输出 `4` 个 lens
- 但 `confidence` 必须下降
- `degradedByInput` 要如实标明

#### 后端如何采信和修正

后端会依据最终 `novelType` 从 [`novel_types.py`](../packages/schemas/common/novel_types.py) 取出固定的 4 个 lens 定义。

无论模型返回得是否完整，后端最终都会保证：

- `items` 覆盖该类型的全部 `4` 个 lens
- 每个 lens 至少有一条证据
- 若模型没给 `summary`，后端按类型自动生成
- `overallConfidence` 取 `4` 个 lens 条目中的最小置信度兜底

这意味着 `type_lens` 的结构完整性主要由后端兜底，而不是完全依赖模型自觉。

#### 重试与失败

- schema 校验最多尝试 `2` 次。

### 7. `consistency_check`

实现入口：

- [`run_consistency_check`](../packages/application/scoring_pipeline/consistency_service.py)

这一步不发模型请求，完全是后端规则检查。

#### 它要解决什么

在 `rubric` 和 `type_lens` 都出来后，系统要先确认这些中间结果是不是“还能继续用”：

- 正文与大纲是否像同一部作品
- 某些轴是不是根本缺了
- 某些高强度结论是不是缺证据
- 有没有重复处罚同一种风险

#### 具体检查项

1. 正文与大纲题材冲突
   - 只有 `chapters_outline` 才会做
   - 会用关键词推断正文和大纲的题材信号
   - 若双方都是“强且唯一”的题材信号，且互相矛盾，就判为高严重度冲突
2. 弱证据项
   - `rubric` item 的 `confidence < 0.3`
3. 无依据结论
   - `reason` 里有“证据充分”“结论明确”“显著优势”等强断言
   - 但 `evidenceRefs` 缺失，或证据置信度过低，或证据只是占位文本
4. 重复处罚
   - 多个轴重复命中 `staleFormula` 或“重复处罚”信号
5. 缺少必需评价轴
   - `missingRequiredAxes` 非空

#### 它如何影响主链

如果出现以下任一情况，主链会在这里直接阻断，不再进入 `aggregation`：

- 正文与大纲高置信冲突
- 无依据结论
- 缺少必需轴

阻断后抛出 `PipelineBlockedError`：

- 跨输入冲突 -> `JOINT_INPUT_MISMATCH`
- 其他阻断 -> `RESULT_BLOCKED`

如果只是弱证据、疑似分歧、重复处罚，则不一定阻断，但会压低 `consistency.confidence`，后续仍会影响整体结果。

### 8. `aggregation`

实现入口：

- [`execute_aggregation`](../packages/application/scoring_pipeline/aggregation_executor.py)

Prompt 选择：

- `chapters_outline + full` -> [`aggregation-default`](../prompts/scoring/aggregation/aggregation-default/v1.md)
- `* + degraded` -> [`aggregation-degraded`](../prompts/scoring/aggregation/aggregation-degraded/v1.md)

#### 这次请求要解决什么

`aggregation` 不是重新打分，而是把已有阶段结果收束成“可直接投影为最终结果”的总体判断草稿。

输入已经包括：

- `screening`
- `typeClassification`
- `rubric`
- `typeLens`
- `consistency`
- 原始正文
- 原始大纲

所以这一步的职责是“收束”和“表述”，不是重新发明事实。

#### 发给模型的 `user_payload`

```json
{
  "taskId": "...",
  "title": "...",
  "chapters": ["..."],
  "outline": "...",
  "screening": { "...": "screening 全量结果" },
  "typeClassification": { "...": "type classification 全量结果" },
  "rubric": { "...": "rubric 全量结果" },
  "typeLens": { "...": "type lens 全量结果" },
  "consistency": { "...": "consistency 全量结果" }
}
```

#### Prompt 要模型怎么评

Prompt 要求模型输出：

- `overallVerdictDraft`
- `verdictSubQuote`
- `overallSummaryDraft`
- `platformCandidates`
- `marketFitDraft`
- `strengthCandidates`
- `weaknessCandidates`
- `riskTags`
- `overallConfidence`

其中最关键的约束是：

- 不重新打分
- 不输出旧字段
- 不把阻断或低置信输入包装成乐观结论
- `degraded` 路线必须直接承认输入受限

#### 后端如何采信和修正

后端只会在满足最基本结构条件时采信这份聚合结果：

- `overallVerdictDraft` 必须非空
- `overallSummaryDraft` 必须非空
- `marketFitDraft` 必须非空

如果这三个核心字段缺失，schema 这一步就会失败。

后端还会：

- 规范化 `platformCandidates`
  - 必须是对象数组
  - `name`、`pitchQuote` 必须非空
  - `weight` 必须是 `0-100` 整数
- 规范化 `strengthCandidates` / `weaknessCandidates`
- 规范化 `riskTags`
- 若 `overallConfidence` 无效，则回退到 `consistency.confidence`

#### 重试与失败

- schema 校验最多尝试 `2` 次。

### 9. `final_projection`

实现入口：

- [`build_final_projection`](../packages/application/scoring_pipeline/projection_service.py)

这一步不再发模型请求，完全是后端把 stage 结果投影成前端正式结果。

#### 它做了什么

1. 把 `rubric.items` 投影成前端 `axes`
2. 把 `aggregation` 的总体判断草稿投影成 `overall`
3. 把 `type_classification + type_lens` 投影成 `typeAssessment`

#### 8 轴如何变成最终分数

每个 `scoreBand` 会被映射成一个固定分数：

- `"0"` -> `20`
- `"1"` -> `35`
- `"2"` -> `55`
- `"3"` -> `75`
- `"4"` -> `90`

#### `overall.score` 如何计算

当前公式是：

1. 先算 8 轴平均分 `universal_base`
2. 再算 4 个 type lens 平均分 `lens_base`
3. 决定类型权重：
   - 若最终类型是 `general_fallback`，type 权重为 `0.15`
   - 否则为 `0.25`
4. 基础总分：
   - `universal_base * (1 - type_weight) + lens_base * type_weight`
5. 再扣规则惩罚：
   - `degraded` -> `-8`
   - `duplicatedPenaltiesDetected` -> `-3`
   - 存在 `WEAK_EVIDENCE` 冲突 -> `-4`
6. 最终分数被夹在 `0-100`

#### 最终结果长什么样

最终公开结果是 [`EvaluationResult`](../packages/schemas/output/result.py)：

- `overall`
- `axes`
- `optional typeAssessment`

其中：

- `overall` 的文字内容来自 `aggregation`
- `axes` 的逐轴分数和理由来自 `rubric`
- `typeAssessment` 的类型、置信度和 4 个 lens 来自 `type_classification + type_lens`

## 任务状态是怎么推进的

任务推进入口在 [`EvaluationService.execute_task`](../packages/application/services/evaluation_service.py)。

### 成功路径

1. `queued + not_available`
2. `start_task` -> `processing + not_available`
3. `run_screening`
4. `_sync_task_with_screening`
5. `run_type_classification`
6. `sync_task_with_type_classification`
7. `run_after_type_classification`
8. `complete_task_with_projection`
9. `completed + available`

### 什么时候会变成 `blocked`

主链抛出 `PipelineBlockedError` 时：

- screening 结果不允许继续
- consistency 检测到跨输入冲突
- consistency 检测到无依据结论
- consistency 检测到缺少必需轴

最终状态是：

- `status=completed`
- `resultStatus=blocked`

并且 `GET /api/tasks/{taskId}/result` 不会返回伪结果，只会返回阻断消息。

### 什么时候会变成 `failed`

主链抛出 `PipelineFailureError` 或发生未捕获异常时：

- provider 调用失败
- timeout
- dependency unavailable
- contract invalid
- stage schema invalid
- internal error

最终状态是：

- `status=failed`
- `resultStatus=not_available`

## 什么时候能拿到正式结果

只有当任务走到 `complete_task_with_projection` 并成功保存 [`EvaluationResultResource`](../packages/schemas/output/result.py) 时，`GET /api/tasks/{taskId}/result` 才会返回：

- `resultStatus=available`
- `resultTime`
- `result`

在此之前：

- `queued / processing` 只会看到 `not_available`
- `blocked` 只会看到阻断消息
- `failed` 只会看到不可展示消息

## 当前这套主链的评价分工

把整条链压缩成一句话：

- `screening` 判断“能不能评”
- `type_classification` 判断“更像哪一类”
- `rubric` 判断“通用 8 轴表现如何”
- `type_lens` 判断“该题材专属兑现如何”
- `consistency` 判断“这些中间结论能不能继续信”
- `aggregation` 判断“怎么把已有结论收束成总体判断”
- `final_projection` 判断“如何投影成前端正式结果”

它不是一个“大 Prompt 一次出总分”的系统，而是一条多阶段、强约束、强后处理、允许阻断的结构化评测流水线。
