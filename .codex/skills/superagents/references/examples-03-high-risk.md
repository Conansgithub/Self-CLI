# 示例 03：高风险变更（risk_level=high/critical）


目标：演示高风险变更如何通过门禁（证据链 + 回滚 + 发布/迁移说明）。

## 场景

数据库迁移 / 权限改动 / 支付链路调整 / 生产操作等。

## 步骤要点（差异点）

1) 在 `superagents/tasks/<name>/change/change.md` 中设置：

- `risk_level: high`（不确定向上取更高等级）
- `risk_flags: "data_migration, payment"`（示例）

2) 高风险门禁会额外强制：

- `change.status` 推进到 `approved/in_progress/done` 前：
  - 影响分析、验收标准变更、风险与缓解、回滚方案必须有内容
  - `发布/灰度计划（如适用）`、`兼容性/迁移` 必须明确（允许写“不适用”，但要说明原因）
- `run.status=success` 时：
  - “证据（日志/截图/命令输出）”段必须有内容
  - `revision/code_refs` 不能为空（可定位代码版本）

3) 推荐操作顺序：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
python3 .codex/skills/superagents/scripts/sa_new_run.py --name <NNNNNN_type_slug>
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```

## 常见失败点

- 高风险但缺少发布/迁移说明（即便“不适用”也要写清原因）
- 验证成功但无证据段内容（审计链断裂）
