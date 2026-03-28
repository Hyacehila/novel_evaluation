# 前后端边界说明（前端相关）

## 核心原则

- Prompt 只在后端治理
- Provider 只在后端治理
- 文件解析只在后端完成
- 前端只消费后端校验后的结构化结果

## 前端负责

- 采集标题、正文、大纲
- 采集上传文件
- 边界内校验
- 读取 provider 状态
- 在缺少启动期 key 时提交 runtime key
- 创建任务
- 轮询任务状态
- 读取结果
- 读取历史

## 后端负责

- 解析上传文件
- 管理 provider 运行状态与 runtime key
- 构建任务
- 持久化任务与结果
- 推进用户任务执行
- 维护状态机
- 返回错误码与诊断相关字段

## 结果边界

前端可展示：

- `overall.score / overall.verdict / overall.summary`
- `overall.platformCandidates / overall.marketFit`
- `axes[*].score / scoreBand / summary / reason / degradedByInput / riskTags`
- 版本元信息
- 市场判断
- provider 状态语义

前端不可展示为正式结果的内容：

- 未经校验的原始模型输出
- `blocked` 或 `not_available` 场景下的伪结果
- 旧版结果结构自动脑补出的“兼容结果”

## Provider 配置边界

前端只做：

- 读取 `GET /api/provider-status`
- 在缺少启动期 key 时调用 `POST /api/provider-status/runtime-key`
- 根据 `canAnalyze / canConfigureFromUi` 决定 UI 是否可提交

后端负责：

- 决定是否允许分析
- 校验 runtime key 格式
- 强制本机访问限制
- 决定配置是否已锁定

## 上传边界

前端只做：

- 存在性校验
- 格式校验
- 大小校验

后端负责：

- `TXT/MD/DOCX` 解析
- `chaptersFile/outlineFile` 业务映射
- `UNSUPPORTED_UPLOAD_FORMAT / UPLOAD_TOO_LARGE / UPLOAD_PARSE_FAILED`

## 历史页边界

前端读取并驱动：

- `q`
- `status`
- `cursor`
- `limit`

后端负责保证：

- `q` 只做标题子串搜索
- `status` 只接受任务状态枚举
- `cursor` 为不透明游标
