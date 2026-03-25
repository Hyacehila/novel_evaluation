# 文件上传与摄取边界

## 文档目的

本文档冻结 `POST /api/tasks` 的上传语义、文件格式矩阵、解析边界和请求边界错误码。

## 提交模式

`POST /api/tasks` 同时支持：

- `application/json`
- `multipart/form-data`

说明：

- 两种模式都必须映射到同一业务请求对象
- 上传模式不改变任务状态语义

## 上传字段

`multipart/form-data` 固定字段为：

- `title`
- `sourceType`
- `chaptersFile`
- `outlineFile`

## 支持格式

上传文件格式固定为：

- `TXT`
- `MD`
- `DOCX`

当前不支持：

- `PDF`
- 图片
- 压缩包
- 富文本编辑器私有格式

## 文件大小

- 默认单文件大小上限固定为 `10 MiB`
- 环境变量覆盖固定为 `NOVEL_EVAL_UPLOAD_MAX_BYTES`

## 前后端职责

### 前端负责

- 校验文件是否存在
- 校验格式是否属于 `TXT/MD/DOCX`
- 校验大小是否超限
- 提交 `multipart/form-data`

### 后端负责

- 解析文件并抽取文本
- 将抽取结果映射为正式输入对象
- 对解析失败返回结构化错误

## 映射规则

- `chaptersFile` 在 `Phase 1` 一律映射为单个 `chapters[0]` 文本块
- `outlineFile` 映射为 `outline.content`
- `Phase 1` 不做自动多章节拆分

## DOCX 解析规则

`DOCX` 仅提取正文段落文本，明确忽略：

- 图片
- 批注
- 修订痕迹
- 页眉页脚样式信息

## 请求边界错误码

新增并冻结以下错误码：

- `UNSUPPORTED_UPLOAD_FORMAT`
- `UPLOAD_TOO_LARGE`
- `UPLOAD_PARSE_FAILED`

约束：

- 这些错误都属于请求边界错误，不创建任务
- HTTP 映射以 `400` 或 `422` 为主

## 与其它文档的关系

- API 资源语义见 `apps/api/contracts/api-v0-overview.md`
- 状态与错误见 `apps/api/contracts/job-lifecycle-and-error-semantics.md`
- 前端输入边界见 `docs/contracts/frontend-input-and-submit-spec.md`
