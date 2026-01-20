# 示例 05：迁移与自检（sa_migrate / sa_doctor）


目标：演示如何把旧文档补字段/升级 schema，并做环境与目录自检。

## 自检（建议先做）

```bash
python3 .codex/skills/superagents/scripts/sa_doctor.py
```

## 迁移（建议先 dry-run）

```bash
python3 .codex/skills/superagents/scripts/sa_migrate.py --upgrade --dry-run
python3 .codex/skills/superagents/scripts/sa_migrate.py --upgrade
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```
