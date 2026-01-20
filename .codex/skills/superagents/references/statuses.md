# superagents 状态枚举（建议）

## specs（规范）

`draft` → `active` → `deprecated`

解释：
- `draft`：起草中，验收不稳定
- `active`：已生效，开发与验收以此为准
- `deprecated`：已废弃，仅用于历史追溯

---

## change（变更）

`draft` → `review` → `approved` → `in_progress` → `done`（或 `rejected` / `canceled`）

解释：
- `draft`：起草中
- `review`：评审中
- `approved`：已批准进入实施
- `in_progress`：实施中
- `done`：实施完成且验证通过
- `rejected`：评审拒绝
- `canceled`：批准后取消

---

## plan（执行方案包）

`planned` → `in_progress` → `done`（或 `blocked` / `canceled`）

解释：
- `planned`：已拆解但未开工
- `in_progress`：实施中
- `done`：实施完成（需有 runs 记录）
- `blocked`：阻塞（需记录原因与解除条件）
- `canceled`：取消

---

## run（执行记录）

`success` / `partial` / `failure`

解释：
- `success`：验证通过
- `partial`：部分成功（需明确未完成项/风险）
- `failure`：失败（需记录原因/回滚/后续）

---

## 评分字段（建议）

评分规则见：`superagents/.sa/wiki/scoring.md`。

- `tasks/*/change/change.md`：`clarity_score: 0-10`（建议 `>=7` 再推进到 `approved`）
- `tasks/*/plan/task.md`：`readiness_score: 0-10`（建议 `>=7` 再推进到 `in_progress`）
