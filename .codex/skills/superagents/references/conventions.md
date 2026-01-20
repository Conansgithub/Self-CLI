# superagents 约定（v1）

本文件定义 superagents 的目录契约、术语、命名规则与最小元数据。

---

## 术语

### domain（业务域/责任域）

按“业务语义 + 数据边界 + 责任团队/Owner”划分的稳定边界。

示例：
- `account`（账号与权限）
- `order`（订单）
- `payment`（支付）
- `inventory`（库存）
- `notify`（通知消息）

### capability（能力/用例能力）

在某个 domain 内，对外提供的一项可被验收的能力，通常能写清“输入/输出/规则/验收用例”。

示例（domain=payment）：
- `create-payment`（发起支付）
- `refund`（退款）
- `reconcile`（对账）

### module（实现模块/工程单元）

代码实现层的边界（包/目录/服务/组件），服务拆分/部署调整会影响 module，但不应反推 domain 边界。

示例：
- `services/payment-service/`
- `pkg/auth/`
- `apps/api-gateway/`

---

## 目录契约

仅以下两类目录允许写“必须/应该/验收标准”（规范SSOT）：

- `superagents/specs/`
- `superagents/tasks/*/change/`

其余（`tasks/*/plan/`、`tasks/*/runs/`、`.sa/wiki/` 等）不得成为规范来源，避免“执行文档漂移成规范”。

推荐布局：

```
superagents/
  specs/<domain>/<capability>/spec.md
  tasks/<NNNNNN>_<type>_<slug>/change/change.md
  tasks/<NNNNNN>_<type>_<slug>/plan/task.md
  tasks/<NNNNNN>_<type>_<slug>/runs/<timestamp>.md
  .sa/history/YYYY-MM/...
  .sa/wiki/...
  .sa/templates/...
```

---

## 命名规则

对象目录命名：`{NNNNNN}_{type}_{slug}`

- `NNNNNN`：6 位补零递增号（脚本维护 `superagents/.sa/registry.json`）
- `type`：建议枚举
  - `feat` 新功能
  - `fix` 缺陷修复
  - `refactor` 代码重构
  - `perf` 性能优化
  - `docs` 文档调整
  - `chore` 杂项/工程化
  - `security` 安全相关
  - `test` 测试相关
- `slug`：kebab-case，建议匹配：`^[a-z0-9]+(-[a-z0-9]+)*$`

---

## 最小元数据（Frontmatter）

建议所有核心文档顶部包含 YAML Frontmatter，最小字段如下：

```yaml
id: CHG-000123  # tasks 的 change/plan/runs（specs 可用 SPEC-000123）
schema_version: 1
title: add release automation
status: draft|active|done|deprecated
owners:
  - "@team-or-person"
links:
  - type: spec|change|plan|run|code|issue
    ref: superagents/tasks/000123_feat_add-release-automation/change
created_at: "2026-01-15"
updated_at: "2026-01-15"
```

建议用于质量门禁的评分字段（可选，但推荐）：

```yaml
# tasks/<name>/change/change.md
clarity_score: 0   # 0-10（见 superagents/.sa/wiki/scoring.md）

# tasks/<name>/plan/task.md
readiness_score: 0 # 0-10（见 superagents/.sa/wiki/scoring.md）
```

建议用于建立追溯链的引用字段（推荐）：

```yaml
# tasks/<name>/change/change.md
spec_refs: "payment/refund, account/auth"

# tasks/<name>/plan/task.md
spec_refs: "payment/refund"
```

建议用于风险治理的字段（推荐）：

```yaml
# tasks/<name>/change/change.md
risk_level: low|medium|high|critical
risk_flags: "payment, data_migration"
```

对于 `specs/*/*/spec.md`，建议额外包含：

```yaml
domain: payment
capability: refund
```

当 `spec.schema_version >= 2` 且 `spec.status=active` 时，建议 AC 使用稳定编号并保持唯一，例如：

```
- [ ] AC-001: ...
- [ ] AC-002: ...
```

当 `spec.schema_version >= 3` 且 `spec.status=active` 时，建议 FR/NFR 也使用稳定编号并保持唯一，例如：

```
### MUST
- [ ] FR-001: ...

### 安全
- [ ] NFR-001: ...
```
