# `evals/runners`

## 子模块角色

该目录用于放置评测执行入口说明与后续 runner 脚本，是回归执行合同入口。

## 当前仓库现实

- 当前目录只有 README
- 还没有任何正式 runner 脚本
- 因此当前这里定义的是 runner 最小输入 / 输出 / 失败分类合同，而不是现成执行系统

## Runner Contract

每个 runner 至少应回答：

- 输入是什么
- 输出是什么
- 失败如何分类
- 报告产物落到哪里
- 何时应该运行
- 命令如何有限结束

## 最小输入

- 数据集引用或 `caseId` 集合
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`
- 执行模式（局部 / 受控回归）

## 最小输出

- `EvalRecord[]` 或等价结构化记录
- 报告引用或报告对象
- baseline 比较结论
- 结构合法性结论

## 失败分类

runner 至少应区分：

- 输入错误
- 业务阻断
- 技术失败
- 结构校验失败
- 报告生成失败

## 不负责

- 重新定义任务状态枚举
- 重新定义正式结果字段
- 跳过 baseline 直接把新结果宣布为正式稳定版本
- 把长时间常驻服务当作唯一 runner 形态

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "输入|输出|失败分类|报告|baseline|终止型" evals/runners/README.md evals/README.md docs/operations/quality-gates-and-regression.md`

## DevFleet 使用约束

- runner 相关 mission 必须指明输入源、输出目录和终止型入口
- 在脚本尚未落地前，不得把 README 合同误写成“当前已有 runner 实现”
