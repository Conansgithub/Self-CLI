# superagents 风险分级与门禁（v1）

风险治理的目标是：**让高风险变更显式化，并强制留下可回滚/可验证/可审计的证据链**。

## risk_level（建议）

枚举：

- `low`：低风险（局部改动、易回滚、影响面清晰）
- `medium`：中风险（跨模块或影响面较大，但可控）
- `high`：高风险（数据迁移/权限/支付/核心链路/外部依赖等）
- `critical`：极高风险（生产操作、不可逆变更、破坏性动作、敏感数据/密钥等）

不确定时建议 **向上取更高等级**。

## risk_flags（可选）

用于记录风险来源，建议用英文逗号分隔，例如：

`data_migration, payment, breaking_change`

## 与门禁的关系（建议）

当 `risk_level in {high, critical}`：

- `change.status` 推进到 `approved/in_progress/done` 前，建议写清：影响分析、回滚方案、验收标准变更、风险与缓解
- `plan.status` 推进到 `in_progress/done` 前，建议写清：实施步骤、验证计划、回滚计划、风险与缓解
- `plan.status=done` 时必须存在 `runs` 且至少 1 条 `run.status=success`，并包含证据位置

