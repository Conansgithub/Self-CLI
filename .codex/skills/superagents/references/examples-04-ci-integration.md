# 示例 04：CI / 本地统一检查入口（sa_check）


目标：把 superagents 的门禁变成 CI 可执行的检查项。

## 本地（开发者）

1) 自动更新 generated（索引/编译产物）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

2) 检查（不写入 generated）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

## CI（建议）

在 CI 中直接运行（失败即阻止合并）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
```

## 常见失败点

- CI 失败提示 “generated 文件需要更新”：说明提交里没包含 `superagents/.sa/wiki/*generated*` 与 `catalog.generated.json` 的更新
