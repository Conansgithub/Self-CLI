# superagents 状态枚举（v2）

> 说明：本文件是建议枚举；校验脚本会按这些枚举进行结构校验。

---

## specs（规范）

`draft → active → deprecated`

---

## change（变更）

`draft → review → approved → in_progress → done`（或 `rejected` / `canceled`）

---

## plan（执行方案）

`planned → in_progress → done`（或 `blocked` / `canceled`）

---

## run（执行记录）

`success` / `partial` / `failure`

---

## 评分字段（建议）

评分规则见：`superagents/.sa/wiki/scoring.md`。

- `tasks/*/change/change.md`：`clarity_score: 0-10`（建议 `>=7` 再推进到 `approved`）
- `tasks/*/plan/task.md`：`readiness_score: 0-10`（建议 `>=7` 再推进到 `in_progress`）
