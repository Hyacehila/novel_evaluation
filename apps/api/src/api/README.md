# `apps/api/src/api`

该目录是后端 FastAPI 应用包。

## 主要文件

- `app.py`：应用创建、日志初始化和生命周期钩子
- `routes.py`：HTTP 路由与接口资源
- `dependencies.py`：仓储、Prompt runtime、Provider 和应用服务装配
- `sqlite_repository.py`：SQLite 持久化实现与默认数据库路径解析
- `upload_parsing.py`：`TXT / MD / DOCX` 上传解析
- `errors.py`：统一错误映射与异常处理

## 运行方式

- 开发启动：`uv run --project apps/api uvicorn api.app:app --reload --host 127.0.0.1 --port 8000`
