# 仓库重构收口清单

本清单用于记录当前仓库从“结构搭建”进入“可交付收口”的状态。

## 已完成

- [x] 顶层目录与边界冻结
- [x] 正式 schema、应用层、API、provider runtime、prompt runtime 落地
- [x] SQLite 持久化与 history 查询落地
- [x] worker eval / batch 与 eval artifacts 落地
- [x] web 五页闭环、query hooks、表单与上传边界落地
- [x] README、运行配置、smoke、rollback 与质量门禁同步到当前实现

## 当前状态

- `Doc-Ready = Yes`
- `DevFleet-Ready = Yes`
- `Implementation-Ready = Yes`
- `Runtime-Ready = Yes`
- `Delivery-Ready = Partial`

## 当前剩余项

- [ ] 在全新环境按文档完成一次安装、启动、smoke 与回滚演练
- [ ] 演练完成后再把阶段正式上调为 `Delivery-Ready = Yes`
