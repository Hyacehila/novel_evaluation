## 变更摘要

- 

## 文档影响

取值：`已同步` / `无需同步` / `待确认`

- 

## 验证

- [ ] `git diff --check`
- [ ] `uv run --project apps/api pytest apps/api/tests evals/tests`
- [ ] `uv run --project apps/worker pytest apps/worker/tests`
- [ ] `pnpm --dir apps/web test`
- [ ] `pnpm --dir apps/web build`

涉及前端流程、provider 状态或真实模型链路时补跑：

- [ ] `pnpm --dir apps/web test:e2e`
- [ ] 真实 DeepSeek auth smoke 或 full pipeline

## 维护者复核点

- [ ] API、Schema、状态、错误码或结果结构与文档一致
- [ ] 环境变量、启动脚本、端口、数据库路径或 provider 配置与文档一致
- [ ] Prompt ID、registry/version/scoring 文件、evals 或 worker 行为与文档一致
- [ ] Markdown 本地链接仍有效，未引入旧路径、旧字段或真实 API key
- [ ] 子项目 README 未复制深层契约，根 README 未重复维护架构细节
