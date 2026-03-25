# DevFleet Mission DAG

## 文档目的

本文档定义 `I1-I9`、`R1-R5`、`E1`、`F1-F2`、`O1-O2` 的依赖顺序、并行边界和禁止并行修改面。

## 波次 DAG

### Wave 0：Implementation-Prep 基础并行

可并行：

- `I1`
- `I2`
- `I3`

说明：

- 三者互不依赖
- 不得并行改动 `packages/application/services/evaluation_service.py`

### Wave 1：Prompt 资产实例化

- `I4`

依赖：

- `I3`

### Wave 2：application 去硬编码化

- `I5`

依赖：

- `I2`
- `I3`

### Wave 3：最小执行入口

可并行：

- `I6`
- `I7`
- `I8`

依赖：

- `I6 <- I5`
- `I7 <- I5`
- `I8 <- I1, I4`

### Wave 4：implementation-prep 复审

- `I9`

依赖：

- `I6`
- `I7`
- `I8`

### Wave 5：Runtime Completion

并行起点：

- `R1`
- `R2`
- `R3`

后续串联：

- `R4 <- R1, R2, R3`
- `R5 <- R1, I6`

### Wave 6：Evals / Worker 闭环

- `E1`

依赖：

- `R2`
- `R3`
- `R4`
- `R5`

### Wave 7：Frontend 闭环

- `F1 <- I6, R5`
- `F2 <- F1, R4, R5`

### Wave 8：Release / Ops

- `O1 <- R1, R5, F2`
- `O2 <- E1, O1`

## 依赖矩阵

| Mission | depends_on |
| --- | --- |
| `I1` | 无 |
| `I2` | 无 |
| `I3` | 无 |
| `I4` | `I3` |
| `I5` | `I2`、`I3` |
| `I6` | `I5` |
| `I7` | `I5` |
| `I8` | `I1`、`I4` |
| `I9` | `I6`、`I7`、`I8` |
| `R1` | `I5`、`I6` |
| `R2` | `I2`、`I5` |
| `R3` | `I3`、`I4` |
| `R4` | `R1`、`R2`、`R3` |
| `R5` | `R1`、`I6` |
| `E1` | `R2`、`R3`、`R4`、`R5` |
| `F1` | `I6`、`R5` |
| `F2` | `F1`、`R4`、`R5` |
| `O1` | `R1`、`R5`、`F2` |
| `O2` | `E1`、`O1` |

## 禁止并行修改面

### 1. 共享 schema 真源

涉及：

- `packages/schemas/output/*.py`
- `packages/schemas/stages/*.py`
- `packages/schemas/evals/*.py`
- `docs/contracts/canonical-schema-index.md`

唯一 owner：

- `I1`
- `R4`

### 2. application 主用例边界

涉及：

- `packages/application/services/evaluation_service.py`
- `packages/application/ports/*.py`

唯一 owner：

- `I5`
- `R1`
- `R4`

### 3. API 资源语义与上传/历史边界

涉及：

- `apps/api/src/api/*.py`
- `apps/api/contracts/*.md`

唯一 owner：

- `I6`
- `R5`

### 4. Prompt 运行时与资产绑定

涉及：

- `packages/prompt-runtime/**`
- `prompts/registry/**`
- `prompts/versions/**`
- `prompts/scoring/**`

唯一 owner：

- `I3`
- `I4`
- `R3`

### 5. Provider 契约与 adapter

涉及：

- `packages/provider-adapters/**`
- `docs/contracts/provider-execution-contract.md`

唯一 owner：

- `I2`
- `R2`

### 6. Worker / Evals 报告闭环

涉及：

- `apps/worker/**`
- `evals/runners/**`
- `evals/reports/**`
- `evals/baselines/**`

唯一 owner：

- `I7`
- `I8`
- `E1`

### 7. Frontend 工程壳与页面

涉及：

- `apps/web/**`

唯一 owner：

- `F1`
- `F2`

## 合并顺序建议

1. `I1`、`I2`、`I3`
2. `I4`
3. `I5`
4. `I6`、`I7`、`I8`
5. `I9`
6. `R1`、`R2`、`R3`
7. `R4`
8. `R5`
9. `E1`
10. `F1`
11. `F2`
12. `O1`
13. `O2`
