# `prompts/scoring`

该目录用于存放小说评分相关 Prompt 资产。

## 子目录职责

- `system/`：系统级评分 Prompt
- `rubric/`：评分维度、评分标准、裁判口径相关 Prompt
- `templates/`：可复用的 Prompt 模板与变量骨架

## 原则

- 文件只承载 Prompt 资产本体
- 使用、加载、渲染与治理应由后端运行时负责
