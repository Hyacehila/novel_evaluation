# `evals/runners`

该目录用于放置回归执行入口说明与后续 runner 脚本。

## 正式输入

- `caseId` 或 case 集合
- `promptVersion`
- `schemaVersion`
- `rubricVersion`
- `providerId`
- `modelId`

## 正式输出

- `EvalRecord[]`
- `EvalReport`
- `EvalBaseline` 比较结论

## 失败分类

- 输入错误
- 业务阻断
- 技术失败
- 结构校验失败
- 报告生成失败

## 规则

- runner 必须是终止型命令
- runner 不重新定义状态机
