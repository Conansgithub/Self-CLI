# superagents 约定（v2）

本文件定义 superagents 的目录契约、术语、命名规则与最小元数据。

---

## 术语

### domain（业务域/责任域）

按业务语义 + 数据边界 + 责任归属划分的稳定边界。

示例：`account` / `order` / `payment` / `inventory` / `notify`

### capability（能力/用例能力）

在某个 domain 内，对外提供的一项可验收能力（能写清输入/输出/规则/验收用例）。

示例（domain=payment）：`create-payment` / `refund` / `reconcile`

### module（实现模块/工程单元）

代码实现层的边界（包/目录/服务/组件）。module 可能变化，但不应反推 domain 边界。

---

## 目录契约（SSOT）

仅以下两类位置允许写“必须/应该/验收标准”（规范SSOT）：

- `superagents/specs/`
- `superagents/tasks/*/change/`

其余（`tasks/*/plan/`、`tasks/*/runs/`、`.sa/wiki/` 等）不得成为规范来源。

---

## 命名规则

对象目录命名：`{NNNNNN}_{type}_{slug}`

- `NNNNNN`：6位补零递增号（脚本维护 `superagents/.sa/registry.json`）
- `type`：`feat|fix|refactor|perf|docs|chore|security|test`
- `slug`：kebab-case，建议 `^[a-z0-9]+(-[a-z0-9]+)*$`

---

## Frontmatter（最小字段）

建议所有核心文档顶部包含 YAML Frontmatter：

```yaml
id: CHG-000123  # tasks 的 change/plan/runs（specs 可用 SPEC-000123）
schema_version: 1
title: your title
status: draft|review|approved|in_progress|done|...
owners:
  - "@team-or-person"
links: []
created_at: "2026-01-15"
updated_at: "2026-01-15"
```

评分字段（建议）见：`superagents/.sa/wiki/scoring.md`。

---

## 追溯链字段（推荐）

为避免“写完找不到依据/验证不可追溯”，建议在变更与方案中填写：

```yaml
# tasks/<name>/change/change.md
spec_refs: "payment/refund, account/auth"

# tasks/<name>/plan/task.md
spec_refs: "payment/refund"
```

建议使用 `domain/capability` 形式，多个用英文逗号分隔。

---

## 风险字段（推荐）

建议在变更/方案/执行记录中填写 `risk_level`（低/中/高/极高），并在高风险时强制留下回滚与验证证据链：

```yaml
risk_level: low|medium|high|critical
risk_flags: "payment, data_migration"
```

项目内详细规则见：`superagents/.sa/wiki/risk.md`。

---

## spec.schema_version=3 约束（推荐）

当 `spec.status=active` 时，建议：

- FR 保留 `MUST/SHOULD/MAY` 分段，并使用稳定编号（如 `FR-001`），且不重复
- NFR 保留性能/安全/可靠性/可观测性/可维护性分段，并使用稳定编号（如 `NFR-001`），且不重复
- AC 使用稳定编号（如 `AC-001`），且不重复
