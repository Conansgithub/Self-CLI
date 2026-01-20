# superagents 评分与门禁（v1）

本文件定义 superagents 的“头脑风暴/分析”与“执行就绪”评分体系，用于：

- 在评审阶段把不确定性显式化（避免直接开写代码）
- 用可量化的门禁决定是否进入实施
- 让 AI 助手能更稳定地遵守流程与格式

> 约定：评分不是规范本体（SSOT），仅作为推进决策与风险控制手段。

项目落地建议：将评分规则放在 `superagents/.sa/wiki/scoring.md`（`sa_init.py` 会初始化该文件），以便项目内可见、可审计。

---

## 1) Clarity Score（需求清晰度评分，0-10）

用途：用于 `tasks/<name>/change/change.md` 的 `clarity_score`，决定是否允许从 `review` 推进到 `approved`。

评分建议（每项 0/1/2 分，总分 10）：

1. **问题陈述清晰**：问题是什么、为什么现在要改
2. **范围边界清晰**：in/out 明确，不会“越写越大”
3. **验收标准清晰**：至少能说明如何验证（AC 方向明确）
4. **影响分析清晰**：涉及模块/数据/API/用户影响可追踪
5. **回滚可执行**：失败时怎么回退，风险可控

门禁建议：

- `clarity_score >= 7`：允许 `approved`
- `< 7`：保持在 `draft/review`，先补齐信息再推进

---

## 2) Readiness Score（执行就绪评分，0-10）

用途：用于 `tasks/<name>/plan/task.md` 的 `readiness_score`，决定是否允许从 `planned` 推进到 `in_progress`。

评分建议（每项 0/1/2 分，总分 10）：

1. **任务拆解可执行**：按模块/步骤拆解，粒度足够落地
2. **验证计划明确**：单测/集成/回归/人工验证路径明确
3. **风险与缓解明确**：关键风险、监控点、应对策略清晰
4. **回滚计划明确**：回滚步骤与条件明确
5. **依赖已确认**：外部依赖/权限/资源/时间窗等明确

门禁建议：

- `readiness_score >= 7`：允许开始实施（`in_progress`）
- `< 7`：继续完善方案，避免“边写边想”导致返工

---

## 3) 与状态流转的关系（建议）

- `change.status: draft → review → approved`
  - `approved` 前建议满足 `clarity_score >= 7`
- `plan.status: planned → in_progress → done`
  - `in_progress` 前建议满足 `readiness_score >= 7`
- `spec.status: draft → active`
  - `active` 前建议：AC 可验证且边界条件明确

---

## 4) 让评分变成“系统”（建议）

仅靠手填 `clarity_score/readiness_score` 往往会漂移，建议用脚本把“缺口清单 + 自动追问”固定下来：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
```

该脚本会输出：
- 建议分数（suggested）
- 缺口清单（gaps）
- 追问问题（questions）
