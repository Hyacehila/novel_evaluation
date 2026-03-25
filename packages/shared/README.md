# `packages/shared`

## 模块角色

该目录用于存放跨模块共享的基础能力。

## 当前仓库现实

- 当前目录只有 README
- 还没有正式共享模块代码
- 因此这里当前定义的是放置边界，而不是现成 shared 库

## 适合放置的内容

- 配置约定
- 日志上下文
- 错误对象的通用包装能力
- 与业务无关的通用工具函数

## 不适合放置的内容

- 评分领域逻辑
- Prompt 正文
- 页面交互逻辑
- Provider 专有适配逻辑
- 为规避边界而塞进来的“大杂烩工具箱”

## 原则

- 共享基础能力必须保持低业务耦合
- 不能把 `shared` 当作边界不清时的兜底目录
- 若能力已经明显属于 `application`、`schemas`、`prompt-runtime` 或 `provider-adapters`，应放回对应目录

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "配置约定|日志上下文|错误对象|通用工具函数|不适合放置" packages/shared/README.md`

## DevFleet 使用约束

- shared 相关 mission 必须明确新增的是配置、日志、错误还是通用工具
- 不得以 shared 为名跨边界吸收业务主线逻辑
