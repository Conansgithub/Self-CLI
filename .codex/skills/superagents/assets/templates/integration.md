# superagents 项目接入（可选，可移除）（v1）

本文件提供“项目级默认遵守”的最小接入方式，均为 **可选**，且删除 `superagents/` 不影响原项目。

---

## 1) 最小接入：统一检查命令

推荐用单一命令作为本地/CI 的检查入口：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

如需自动更新 generated 产物（索引/编译 JSON）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

---

## 2) CI（示例）

将以下命令加入 CI 步骤即可（不要求改动代码）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

---

## 3) Git Hook（示例，谨慎）

可在 `.git/hooks/pre-commit` 中运行检查（注意：Git hook 不是跨团队自动分发的）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

---

## 4) AGENTS.md（可选片段）

如果你希望 AI 助手“默认先看 superagents”，可在项目的 `AGENTS.md` 增加一段 **可移除** 的约定：

- 规范 SSOT：`superagents/specs/` + `superagents/tasks/*/change/`
- 收口门禁：合并/完成前跑 `sa_check.py`（不写入 generated；需要更新用 `--fix`）
