# `packages/schemas`

## 模块角色

该模块是项目正式结构契约的唯一目标真源目录。

## 当前子域

- `common/`
- `input/`
- `output/`
- `stages/`
- `evals/`

## 主要职责

- 固化字段命名、类型、枚举与必需性
- 为 API、application、worker、evals 提供统一结构
- 为版本治理与兼容性判断提供依据

## 当前口径

- `common/`、`input/`、`output/`、`stages/`、`evals/` 都已在当前仓库中占据正式子域
- API、worker、评测和历史回访应共用这一套结构真源

## DevFleet 使用约束

- 任何 schema 落地都先读 `docs/contracts/canonical-schema-index.md`
- 不允许在 API、前端契约或 evals 文档中反向发明正式字段结构

## 验收方式

- `git diff --check`
- `Get-ChildItem -Recurse -File docs\\contracts,packages\\schemas | Select-String -Pattern 'implemented|doc_frozen|input/|output/|stages/|evals/'`
