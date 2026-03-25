# `evals/cases`

## 子模块角色

该目录用于组织结构化评测用例，是 dataset 与 runner 之间的用例编排入口。

## 当前仓库现实

当前目录下实际存在：

- `scoring/`
- `robustness/`
- `regression/`

但三者当前都只有 `.gitkeep` 占位，没有正式 case 实例文件。

## 子目录职责

- `scoring/`：正常评分能力用例
- `robustness/`：异常输入、边界条件、鲁棒性用例
- `regression/`：版本回归比较用例

## Case Contract

每个正式用例至少应说明：

- `caseId`
- 关联 dataset 或样本引用
- `inputComposition`
- 执行目标
- 预期结果类型
- 比较维度
- 是否进入 baseline

## 原则

- 用例应明确输入、预期和比较维度
- 用例组织应服务于回归执行，而不是临时堆放样本
- 用例不能反向定义正式 schema 字段
- 不得为 `pairwise` 或多路径评分维持单独正式 case 体系

## 验收方式

当前最小验收方式：

- `git diff --check`
- `rg "caseId|inputComposition|baseline|比较维度|预期结果类型" evals/cases/README.md evals/README.md`

## DevFleet 使用约束

- case 相关 mission 必须明确修改的是 `scoring`、`robustness` 还是 `regression`
- 在实例文件尚未落地前，不得把 README 文本误写成“当前已有结构化 case 集”
