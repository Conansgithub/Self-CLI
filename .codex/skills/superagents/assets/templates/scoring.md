# superagents 评分与门禁（v1）

本文件是 superagents 的“头脑风暴/分析”与“执行就绪”评分体系，用于把不确定性显式化并作为推进门禁。

> 约定：评分不是规范本体（SSOT），仅作为推进决策与风险控制手段。

---

## Clarity Score（需求清晰度评分，0-10）

写入位置：`tasks/<name>/change/change.md` 的 `clarity_score`。

评分建议（每项 0/1/2 分，总分 10）：

1. 问题陈述清晰（问题是什么、为什么现在要改）
2. 范围边界清晰（in/out 明确）
3. 验收标准清晰（至少能说明如何验证）
4. 影响分析清晰（模块/数据/API/用户影响可追踪）
5. 回滚可执行（失败时能安全回退）

门禁建议：`clarity_score >= 7` 再推进到 `approved`。

---

## Readiness Score（执行就绪评分，0-10）

写入位置：`tasks/<name>/plan/task.md` 的 `readiness_score`。

评分建议（每项 0/1/2 分，总分 10）：

1. 任务拆解可执行（按模块/步骤拆解）
2. 验证计划明确（单测/集成/回归/人工验证）
3. 风险与缓解明确（关键风险与应对）
4. 回滚计划明确（回滚条件与步骤）
5. 依赖已确认（外部依赖/权限/资源/时间窗）

门禁建议：`readiness_score >= 7` 再将 plan `status` 推进到 `in_progress`。

---

## 评分如何落地成“系统”（建议）

仅靠手填分数会不稳定，建议配合脚本把“缺口清单 + 自动追问”固定下来：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
```

输出包含：
- 建议分数（suggested）
- 缺口清单（gaps）
- 追问问题（questions）
