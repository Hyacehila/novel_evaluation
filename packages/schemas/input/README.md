# `packages/schemas/input`

## 子域角色

该子域用于放置正式输入相关 schema。

## 当前正式对象

当前已经实际落地：

- `packages/schemas/input/manuscript.py`
  - `ManuscriptChapter`
  - `ManuscriptOutline`
  - `Manuscript`
- `packages/schemas/input/joint_submission.py`
  - `JointSubmissionRequest`
- `packages/schemas/input/screening.py`
  - `InputScreeningResult`

## 作用边界

- 冻结联合投稿包输入结构
- 冻结创建任务请求结构
- 冻结输入预检查结构
- 不承接对外正式结果正文结构

## 当前边界说明

- `JointSubmissionRequest` 通过继承 `Manuscript` 复用联合输入主结构
- `InputScreeningResult` 当前保留在 `input/`，用于表达输入充分性、降级与继续执行边界
- 若未来阶段对象需要整体迁移，必须先更新 `docs/contracts/canonical-schema-index.md`

## 不负责

- 定义任务状态与结果状态语义
- 定义正式结果对象
- 定义前端页面 View Model

## 验收方式

- `git diff --check`
- `rg "ManuscriptChapter|ManuscriptOutline|Manuscript|JointSubmissionRequest|InputScreeningResult" docs/contracts/canonical-schema-index.md packages/schemas/input/README.md`
