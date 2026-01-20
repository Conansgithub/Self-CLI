# 示例 02：标准闭环（change → plan → run → check → archive）


目标：演示日常最常用的闭环路径（不强制 spec-first，但仍推荐）。

## 步骤

1) 初始化（首次）：

```bash
python3 .codex/skills/superagents/scripts/sa_init.py
```

2) 新建 change + plan：

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type fix --slug handle-empty-config --title "Handle empty config"
python3 .codex/skills/superagents/scripts/sa_assess.py --name 000001_fix_handle-empty-config
```

3) 补齐门禁字段：

- `spec_refs`：至少填 1 条（如暂无 spec，建议先用 `sa_new_spec.py` 建一个 draft spec，再回填引用）
- `risk_level`：默认 low，不确定向上取更高等级
- `clarity_score/readiness_score`：达到门禁后再推进状态

4) 实施完成后新增 run 记录并写证据：

```bash
python3 .codex/skills/superagents/scripts/sa_new_run.py --name 000001_fix_handle-empty-config
```

5) 收口（状态推进）：

- `run.status=success`
- `plan.status=done`
- `change.status=done`

6) 一键检查与归档：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
python3 .codex/skills/superagents/scripts/sa_archive.py --name 000001_fix_handle-empty-config
```

## 常见失败点

- `change=done` 但 `plan!=done`（或反过来）会被门禁拦截
- `plan.status=in_progress/done` 但关键段落为空（实施步骤/验证计划/回滚计划/风险与缓解）
