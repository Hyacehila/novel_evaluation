# 前端页面规格说明

## 覆盖页面

- 工作台首页
- 新建评测任务页
- 任务详情页
- 结果详情页
- 历史记录页

## 全局规则

- 页面围绕“创建任务 -> 查看状态 -> 查看结果 -> 查看历史”组织
- 正式结果只在 `resultStatus=available` 时展示
- 上传 UX 必须覆盖 `TXT/MD/DOCX`
- 历史页检索必须围绕 `q/status/cursor/limit`

## 工作台首页

展示：

- 最近任务
- 处理中任务
- 最近结果
- 进入新建任务页入口

不展示：

- 完整结果正文

## 新建评测任务页

模块：

- 标题输入
- 正文输入
- 大纲输入
- 上传区
- 提交区

约束：

- 支持 JSON 与 multipart
- 上传字段固定为 `chaptersFile`、`outlineFile`
- 提交中禁用按钮

## 任务详情页

展示：

- `taskId`
- `inputSummary`
- `inputComposition`
- `evaluationMode`
- `status`
- `resultStatus`
- `errorCode/errorMessage`

行为：

- `queued/processing` 时轮询
- 终态后停止轮询

## 结果详情页

展示：

- 四项评分
- 平台推荐
- 编辑结论
- 市场判断
- 详细分析
- 优势与弱点

异常态：

- `blocked`
- `not_available`
- `fetch_failed`

## 历史记录页

展示：

- 标题
- 状态
- 结果可用性
- 创建时间

筛选：

- `q`：标题子串搜索
- `status`：任务状态筛选
- `cursor`：游标分页
- `limit`：默认 `20`
