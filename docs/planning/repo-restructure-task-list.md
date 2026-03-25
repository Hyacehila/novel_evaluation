# 仓库重构收口清单

本清单用于记录当前仓库从“结构搭建”进入“可安全发起窄 mission”的收口状态。

## 已完成

### 1. 目录与边界冻结

- [x] 建立 `apps/`、`packages/`、`prompts/`、`evals/`、`docs/`、`scripts/` 顶层骨架
- [x] 明确 `output/playwright/` 为研究/抓取产物区
- [x] 冻结单主线全 `LLM rubric` 评分路线
- [x] 冻结 `chapters + outline / chapters_only / outline_only` 联合投稿包输入边界

### 2. 文档真源收口

- [x] 冻结 readiness 分层与真源优先级
- [x] 冻结领域模型、阶段契约、状态语义和错误语义
- [x] 建立 `docs/contracts/canonical-schema-index.md`
- [x] 建立正式 `mission-catalog` 与 `mission-dag`
- [x] 建立 `quality-gates` 与 `rollback / fallback` 主文档

### 3. 仓库真实状态同步

- [x] 将 `packages/schemas/` 已落地类同步回文档
- [x] 将 `packages/application/` 与 `apps/api/` 最小实现基线同步回文档
- [x] 将 Prompt / Evals / 模块 README 升级为合同化入口
- [x] 清理前端文档中的旧 `inputType / text / fetch_failed` 误用

## 当前状态

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Not Yet`

## 当前剩余项

以下剩余项已经不属于“仓库重构文档收口”，而属于后续窄 implementation mission：

- [ ] 落地 `packages/schemas/evals/` 正式 schema 类
- [ ] 落地 `packages/provider-adapters/` 最小 provider adapter
- [ ] 落地 `packages/prompt-runtime/` 最小 registry / versions 读取能力
- [ ] 让 `packages/application/` 去除对本地占位 provider / prompt 常量的直接依赖
- [ ] 落地 `apps/worker/` 最小执行入口
- [ ] 落地 `evals/runners/` 最小本地 runner 与报告写出入口

## 后续建议顺序

1. 先按 `devfleet-mission-catalog.md` 认领 Wave 1 窄 mission
2. 再推进 application / API / worker / evals runner 的串接
3. 最后再复审是否达到 `Implementation-Ready`

## 当前不再建议做的事情

- 不再发起“仓库整体重构”这类宽泛任务
- 不再把已经落地的 schema / API 基线重新写回“待开始”
- 不再让 README、前端假契约或 Evals 文档反向定义结构真源
