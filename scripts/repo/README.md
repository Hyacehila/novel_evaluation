# `scripts/repo`

## 子模块角色

该目录用于仓库结构维护与一致性检查脚本。

## 适合放置的脚本

- 目录结构检查
- README / 合同文档锚点检查
- schema / docs / contracts 一致性检查
- 终止型仓库健康检查

## 不适合放置的脚本

- 业务评分主线实现
- 长时运行服务
- 需要人工长时间交互才能完成的流程

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "结构维护|一致性检查|终止型" scripts/repo/README.md scripts/README.md docs/operations/quality-gates-and-regression.md`

## DevFleet 使用约束

- repo 脚本 mission 必须明确检查对象与终止条件
- 不得把临时探索命令直接包装成正式 repo 脚本合同
