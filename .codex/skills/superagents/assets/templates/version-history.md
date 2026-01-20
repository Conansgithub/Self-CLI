# superagents 版本历史（项目内）（v1）

本文件用于记录项目内 superagents 规范/门禁的演进（便于长期维护与团队协作）。

> 约定：本文件记录“你项目里的规范如何变化”，不是上游工具发布日志。

---

## 变更记录

### 2026-01-20

- 初始化：引入 superagents 目录体系（specs/tasks/.sa）
- 门禁：引入 `clarity_score/readiness_score`、`spec_refs`、`risk_level` 与 `runs` 证据链要求
- 机读：引入 `catalog.generated.json`（由 `sa_compile.py` 生成）

---

## 维护建议

- 每次升级 schema、调整门禁规则、调整 SSOT 范围，都在这里追加一条记录
- 记录至少包含：动机、影响范围、迁移方式（是否需要 `sa_migrate.py`）
