---
id: "{{ID}}"
schema_version: 2
title: "{{TITLE}}"
status: planned
spec_refs: ""
risk_level: low
risk_flags: ""
readiness_score: 0
owners:
  - "{{OWNER}}"
links:
  - type: change
    ref: superagents/tasks/{{NAME}}/change
created_at: "{{DATE}}"
updated_at: "{{DATE}}"
---

# {{TITLE}} - 执行方案

## 目标与成功标准

## 就绪检查与评分（Readiness Score）

> 评分规则见：`superagents/.sa/wiki/scoring.md`。建议 `readiness_score >= 7` 再把 `status` 推进到 `in_progress`。

## 任务清单

- [ ] 细化需求与成功标准（引用 specs/ 与 change.md 的验收标准）
- [ ] 拆解任务（按模块/步骤/风险拆分）
- [ ] 实现（含必要的工程化/配置变更）
- [ ] 测试（单测/集成/回归，按项目约定）
- [ ] 可观测性（日志/指标/告警，如适用）
- [ ] 迁移与兼容性处理（如适用）
- [ ] 记录验证结果与证据到 `runs/`
- [ ] 更新 `change.md` / `task.md` 状态为 done
- [ ] 刷新索引与校验（`sa_index.py` / `sa_validate.py`）

## 里程碑 / 检查点

- M1：需求与门禁通过（clarity/readiness 达标）
- M2：核心路径实现完成
- M3：验证通过并写入 runs 证据

## 实施步骤

## 验证计划

## 回滚计划

## 风险与缓解

## 记录
