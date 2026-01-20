# superagents - 项目规范入口

本目录承载本项目的 superagents 规范与执行留痕。

## 目录说明

- `specs/`：规范SSOT（需求/约束/验收标准）
- `tasks/`：任务闭环（每个 task 下面包含 change/plan/runs）
- `.sa/`：superagents 元数据（模板/索引/归档/发号器等；默认隐藏）

## 项目约定入口（建议先读）

- `.sa/wiki/conventions.md`：术语/目录契约/命名与元数据
- `.sa/wiki/workflows.md`：建议工作流
- `.sa/wiki/statuses.md`：状态枚举
- `.sa/wiki/scoring.md`：评分与门禁（`clarity_score/readiness_score`）
- `.sa/wiki/risk.md`：风险分级与门禁（`risk_level`）
- `.sa/wiki/schema-versions.md`：文档 schema_version 说明
- `.sa/wiki/version-history.md`：项目内 superagents 版本历史
- `.sa/wiki/integration.md`：项目接入（可选，可移除）
- `.sa/wiki/troubleshooting.md`：故障排除（报错→原因→修复）

## 快速开始

1) 初始化（首次使用）：

```bash
python3 .codex/skills/superagents/scripts/sa_init.py
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
python3 .codex/skills/superagents/scripts/sa_compile.py
```

2) 新建变更与执行方案：

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type feat --slug your-change-slug --title "你的标题"
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
python3 .codex/skills/superagents/scripts/sa_compile.py
```

3) 执行开发后写入 `tasks/<name>/runs/` 记录，并更新 `change.md` / `task.md` 的 `status`。
