# superagents 风险分级与门禁（v1）

本文件用于把“高风险变更”显式化，并作为推进门禁的一部分。

> 约定：风险分级不是规范本体（SSOT），但会影响是否允许推进状态与收口。

---

## 风险等级（risk_level）

写入位置：`tasks/<name>/change/change.md`（可选同步到 `tasks/<name>/plan/task.md`、`tasks/<name>/runs/*.md`）。

枚举：

- `low`：低风险（局部改动、易回滚、影响面清晰）
- `medium`：中风险（跨模块或影响面较大，但可控）
- `high`：高风险（数据迁移/权限/支付/核心链路/外部依赖等）
- `critical`：极高风险（生产操作、不可逆变更、破坏性动作、敏感数据/密钥等）

建议：不确定时 **向上取更高等级**（保守策略）。

---

## 风险标记（risk_flags，可选）

写入位置：`risk_flags`（英文逗号分隔）。

建议取值（示例）：

- `data_migration`
- `auth`
- `payment`
- `prod_ops`
- `security`
- `external_dependency`
- `breaking_change`

---

## 高风险门禁（建议）

当 `risk_level in {high, critical}` 且准备推进到 `approved/in_progress/done` 时，建议至少满足：

- `change.md`：影响分析、验收标准变更、风险与缓解、回滚方案均已补齐（允许写 “不适用” 的地方必须写清原因）
- `task.md`：实施步骤、验证计划、回滚计划、风险与缓解均已补齐
- `tasks/<name>/runs/`：存在 `status=success` 的 run 记录，且包含验证证据位置（日志/截图/命令输出路径）
- `sa_validate.py` 通过
