# superagents Schema Versions（项目内）（v1）

本文件用于说明项目内 superagents 文档的 `schema_version` 含义与兼容策略。

> 推荐：升级 schema 前先跑 `sa_migrate.py --upgrade --dry-run`（如提供）。

---

## specs/<domain>/<capability>/spec.md

### schema_version=3（推荐）

关键点：
- 结构强校验：必须保留模板二级标题（`## ...`）
- `status=active` 时门禁更严格：
  - AC 必须有编号（`AC-001`）且不重复
  - FR 必须有编号（`FR-001`）且不重复
  - NFR 必须有编号（`NFR-001`）且不重复

---

## tasks/<name>/change/change.md

### schema_version=2（推荐）

新增/要求：
- `spec_refs`（domain/capability，逗号分隔）
- `risk_level`（low/medium/high/critical）
- `risk_flags`（可选，逗号分隔）

门禁（部分）：
- `status in {approved,in_progress,done}` 时：
  - `clarity_score >= 7`
  - `spec_refs` 不能为空且引用的 spec 必须存在
  - 关键段落必须有内容（背景/范围/头脑风暴/影响/验收变更/风险/回滚）
  - 高风险（high/critical）还要求发布/迁移相关段落明确（允许写“不适用”，需说明原因）

---

## tasks/<name>/plan/task.md

### schema_version=2（推荐）

新增/要求：
- `spec_refs`（与 change 保持一致）
- `risk_level`（与 change 保持一致）
- `risk_flags`（可选）

门禁（部分）：
- `status in {in_progress,done}` 时：
  - `readiness_score >= 7`
  - `spec_refs` 不能为空且引用的 spec 必须存在
  - 关键段落必须有内容（实施步骤/验证计划/回滚计划/风险与缓解）

---

## tasks/<name>/runs/<timestamp>.md

### schema_version=2（推荐）

新增/要求：
- `change_name` / `plan_name`（必须与目录名一致）
- `spec_refs`（追溯链）
- `code_refs`（可选）
- `risk_level`（与 change/plan 对齐）

门禁（部分）：
- `status=success` 时：必须填写 `revision` 或 `code_refs`
- `risk_level in {high,critical}` 且 `status=success` 时：证据段必须有内容

---

## generated 产物

- `superagents/.sa/wiki/*-index.generated.md`：由 `sa_index.py` 生成
- `superagents/.sa/wiki/catalog.generated.json`：由 `sa_compile.py` 生成（`schema_version=2`）

---

## 兼容性策略（建议）

- 尽量保持：旧文档不升级也可通过门禁（除非明确要求）
- 如门禁与 schema 必须同步升级：提供迁移脚本（例如 `sa_migrate.py`）并在 `version-history.md` 记录
