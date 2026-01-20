# superagents 项目接入（v1）

目标：让 superagents 在项目里“默认可被遵守”，同时保持 **可撤销**（删除 superagents/ 不影响原项目）。

推荐最小接入：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

可选增强：

- CI 加一条 `sa_check.py`
- pre-commit hook 加一条 `sa_check.py`
- 在项目 `AGENTS.md` 增加一段“SSOT 与门禁”的简短说明
