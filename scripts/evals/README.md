# `scripts/evals`

## 子模块角色

该目录用于评测执行、baseline 生成与报告辅助脚本。

## 适合放置的脚本

- 局部 eval 执行入口
- 受控回归触发脚本
- baseline 生成辅助脚本
- report 汇总辅助脚本

## 不适合放置的脚本

- 正式评分业务主线实现
- 无终止条件的常驻执行器
- 反向定义 schema 或结果结构的脚本

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "评测执行|baseline|报告|受控回归|终止" scripts/evals/README.md scripts/README.md evals/README.md`

## DevFleet 使用约束

- evals 脚本 mission 必须明确输入样本、输出目录和比较对象
- 不得把一次性的探索命令误写成正式 evals harness
