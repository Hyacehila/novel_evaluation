# `scripts/maintenance`

## 子模块角色

该目录用于日常维护、清理和辅助性仓库操作脚本。

## 适合放置的脚本

- 临时产物清理
- 文档与目录辅助维护
- 非业务主线的日常仓库操作

## 不适合放置的脚本

- 删除正式真源以掩盖问题的脚本
- 破坏性强、不可恢复的默认操作
- 直接修改正式业务语义的脚本

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "清理|维护|辅助性仓库操作|破坏性" scripts/maintenance/README.md scripts/README.md docs/operations/rollback-and-fallback.md`

## DevFleet 使用约束

- maintenance 脚本 mission 必须明确作用范围和可回退方式
- 不得把一次性人工命令清单直接包装成正式 maintenance 脚本合同
