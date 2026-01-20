# superagents 工作流（v2）

本工作流围绕三件事组织：

- **规范SSOT**：`specs/` 与 `tasks/*/change/` 承载“必须/应该/验收标准”
- **执行留痕**：`tasks/*/plan/` 拆解执行；`tasks/*/runs/` 记录结果与证据
- **质量门禁**：通过评分与结构校验降低返工

---

## 入口判断（路由）

1) 新增/修改规范 → `specs/`
2) 提出变更（为什么改/影响/验收更新）→ `tasks/*/change/`
3) 实施变更（代码改动/验证/发布）→ `tasks/*/plan/` + `tasks/*/runs/`

如果不确定，先补齐信息再写代码。

---

## 头脑风暴 + 评分（建议先做）

评分规则见：`superagents/.sa/wiki/scoring.md`。

- `change.clarity_score >= 7` 再推进到 `approved`
- `plan.readiness_score >= 7` 再推进到 `in_progress`

建议配合脚本输出缺口与追问清单（让评分变成“系统”）：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
```

---

## Spec（规范）

- 路径：`specs/<domain>/<capability>/spec.md`
- `spec.status: draft → active → deprecated`
- `active` 前确保 AC 可验证且边界条件明确

---

## Change（变更）

- 路径：`tasks/<name>/change/change.md`
- `change.status: draft → review → approved → in_progress → done`
- `approved` 前建议完成：备选方案、`clarity_score`、影响分析、回滚方案

---

## Execution（实施）

- 路径：`tasks/<name>/plan/task.md` + `tasks/<name>/runs/*.md`
- `plan.status: planned → in_progress → done`
- 每次关键验证写一条 run 记录；`done` 必须有 runs 证据

---

## 持续推进闭环（强制）

本体系不以“代码已完成”作为结束条件，而是以 **验证通过 + 留痕完整 + 门禁通过** 作为结束条件。

执行循环（Loop）：

1) **澄清与门禁**：评分不达标（`clarity_score/readiness_score < 7`）时先补齐文档，不推进状态
2) **计划与实施**：按 `task.md` 执行；遇到阻塞写明原因与解除条件
3) **验证与留痕**：每次关键验证都新增 `tasks/<name>/runs/*.md`（写结果与证据）
4) **收口**：至少 1 条 `run.status=success` → `plan=done` → `change=done` → `sa_validate` 通过 → 可选归档

最小 DoD（收口标准）：

- ✅ `sa_validate.py` 通过
- ✅ `tasks/<name>/plan/task.md`：`status=done`
- ✅ `tasks/<name>/change/change.md`：`status=done`
- ✅ `tasks/<name>/runs/`：至少 1 条 `status=success` 且包含证据位置

---

## History（归档）

- 当对象完成后，可用 `sa_archive.py` 归档到 `.sa/history/YYYY-MM/`（默认复制，安全）
  - `python3 .codex/skills/superagents/scripts/sa_archive.py --name <name>`

---

## 最小门禁清单

- 评分是否达标（见 `superagents/.sa/wiki/scoring.md`）
- 影响范围与回滚是否可执行
- AC 是否可验证
- 是否存在高风险动作（数据迁移/权限/支付/生产变更等）

建议在阶段收口时刷新索引与编译产物：

```bash
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
python3 .codex/skills/superagents/scripts/sa_compile.py
```
