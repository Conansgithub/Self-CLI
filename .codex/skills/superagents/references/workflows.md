# superagents 工作流（v2）

本工作流吸收两类“精华”：

- **规范侧**：结构化、可索引、可持续演进（以 specs/changes 作为 SSOT）
- **规范侧**：结构化、可索引、可持续演进（以 specs + tasks/*/change 作为 SSOT）
- **执行侧**：阶段化推进、质量门禁、留痕可审计（tasks/*/plan + tasks/*/runs + .sa/history）

---

## 0. 入口判断（路由）

收到需求时先判断属于哪类：

1) **新增/修改规范** → 走「1. Spec 工作流」
2) **提出变更**（为什么要改、影响、验收更新）→ 走「2. Change 工作流」
3) **实施变更**（代码改动、验证、发布）→ 走「3. Execution 工作流」

如果不确定，优先补齐信息而不是直接写代码。

---

## 0.1 头脑风暴 + 评分（建议先做）

目标：在进入实施前把不确定性显式化，降低返工。

- 头脑风暴与评分规则见：`superagents/.sa/wiki/scoring.md`
- 建议门禁：
  - `change.clarity_score >= 7` 再进入实施准备（`approved`）
  - `plan.readiness_score >= 7` 再开始实施（`in_progress`）

建议配合脚本输出缺口与追问清单（让评分变成“系统”）：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name <NNNNNN_type_slug>
```

---

## 1. Spec 工作流（规范SSOT）

目标：把“必须/应该/验收标准”写进 `superagents/specs/`，并可长期维护。

建议步骤：

1) 确定 `domain` 与 `capability`
2) 用 `superagents/.sa/templates/spec.md` 创建 `specs/<domain>/<capability>/spec.md`
3) 写清：目标/范围/非目标/规则/验收标准（AC）
4) 如果存在外部接口与数据：补充 `api.md` / `data.md`
5) 将 `status` 从 `draft` 推进到 `active` 前，至少满足：
   - AC 可验证（可写成测试用例/场景）
   - 关键边界条件明确

---

## 2. Change 工作流（变更SSOT）

目标：把“为什么改、改什么、影响什么、验收怎么变”写进 `superagents/tasks/*/change/`。

建议步骤：

1) 用脚本创建骨架：

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type feat --slug your-slug --title "Your title"
```

2) 在 `change.md` 中至少补齐：
   - 背景/动机（问题是什么）
   - 头脑风暴（2-3个备选方案与取舍）
   - 评分与门禁（`clarity_score`）
   - 变更内容（做什么）
   - 影响分析（哪些模块/数据/API/用户会受影响）
   - 验收标准变更（新增/修改/删除哪些 AC）
   - 迁移与回滚（如何安全上线/回退）
3) 根据评审推进 `status`：`draft → review → approved`

---

## 3. Execution 工作流（实施与留痕）

目标：把“怎么做、做了什么、验证结果与证据”写进 `tasks/*/plan/` 与 `tasks/*/runs/`，并可审计。

建议步骤：

1) 在 `tasks/<name>/plan/task.md` 拆解任务（按模块/步骤/风险），并填写 `readiness_score`
2) 满足门禁后将 plan `status` 置为 `in_progress` 并开始实施
3) 每次关键验证（单测/集成/回归/压测/人工验证）都在 `tasks/<name>/runs/` 写记录（可多次）
4) 变更完成并验证通过后：
   - `tasks/<name>/runs/*.md` 记录写 `success`
   - plan 置 `done`
   - change 置 `done`
5) 刷新索引与校验：

```bash
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
python3 .codex/skills/superagents/scripts/sa_compile.py
```

---

## 持续推进闭环（强制）

使用本体系时遵循“持续推进直到验证完成”的闭环：**不以“我写完代码了”作为结束条件**，而是以“验证通过 + 留痕完整 + 门禁通过”为结束条件。

执行循环（Loop）：

1) **澄清与门禁**：信息不足或评分不达标（`clarity_score/readiness_score < 7`）时，必须先追问/补齐文档再推进状态
2) **计划与实施**：按 `tasks/*/plan/task.md` 执行；遇到阻塞写明原因与解除条件
3) **验证与留痕**：每次关键验证都新增 `tasks/<name>/runs/*.md` 记录结果与证据
4) **收口**：至少 1 条 `run.status=success` → `plan=done` → `change=done` → `sa_validate` 通过 → 可选 `sa_archive`

最小 DoD（收口标准）：

- ✅ `sa_validate.py` 通过（结构/门禁/状态一致性）
- ✅ `tasks/<name>/plan/task.md`：`status=done`
- ✅ `tasks/<name>/change/change.md`：`status=done`
- ✅ `tasks/<name>/runs/`：至少 1 条 `status=success` 且包含验证证据位置

---

## 质量门禁（最小版）

在进入实施前（approved → in_progress）建议检查：
- `clarity_score/readiness_score` 是否达标（见 `superagents/.sa/wiki/scoring.md`）
- 变更影响范围与回滚是否可执行
- AC 是否可验证（至少能说明怎么验证）
- 是否存在高风险动作（数据迁移/权限/支付/生产变更等）

---

## 4. History（归档）

当对象完成后，可归档到 `superagents/.sa/history/YYYY-MM/` 便于长期追溯（默认复制，安全）：

```bash
python3 .codex/skills/superagents/scripts/sa_archive.py --name 000123_feat_example
```
