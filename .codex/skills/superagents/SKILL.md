---
name: superagents
description: superagents 规范体系与执行闭环（specs + tasks + .sa）以及配套自动化脚本（如递增ID发号）。当项目使用 superagents/ 目录管理规范、变更与执行留痕时使用。
---

# superagents

superagents 定义一套可审计、可自动化、可长期维护的「规范 → 变更 → 执行留痕」标准。

- **规范SSOT**：只有 `specs/` 与 `tasks/*/change/` 承载“必须/应该/验收标准”
- **闭环追溯**：`tasks/*/plan/` 拆解执行；`tasks/*/runs/` 记录结果与证据；`.sa/history/` 归档
- **脚本优先**：重复机械化动作交给 `scripts/`
- **质量门禁**：通过评分（`clarity_score/readiness_score`）与结构校验降低返工
- **可移除**：不侵入原项目结构；删除项目根目录 `superagents/` 不影响原项目

## 快速开始（5 分钟走通闭环）

前置条件：
- Python 3（建议 3.9+）
- 你的项目根目录中能执行：`python3 .codex/skills/superagents/scripts/...`

1) 初始化（只创建 `superagents/`，不改动其他目录）：

```bash
python3 .codex/skills/superagents/scripts/sa_init.py
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```

2) 创建一条 spec（domain/capability）：

```bash
python3 .codex/skills/superagents/scripts/sa_new_spec.py --domain payment --capability refund --title "Refund"
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

3) 创建一条 change + plan（并补齐追溯链与门禁字段）：

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type feat --slug refund-v2 --title "Refund v2"
python3 .codex/skills/superagents/scripts/sa_assess.py --name 000001_feat_refund-v2
```

4) 实施与验证（写 run 记录）：

```bash
python3 .codex/skills/superagents/scripts/sa_new_run.py --name 000001_feat_refund-v2
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```

---

## 目录契约（项目内可见目录：`superagents/`）

```
superagents/
  specs/        # 规范SSOT（需求/约束/验收）
  tasks/        # 任务闭环（每个 task 下含 change/plan/runs）
  .sa/          # 元数据（发号器/模板/索引/归档；默认隐藏）
    registry.json
    templates/
    wiki/
    history/
```

规范推荐按 `domain/capability` 分层：

- `specs/<domain>/<capability>/spec.md`
- `specs/<domain>/<capability>/api.md`（可选）
- `specs/<domain>/<capability>/data.md`（可选）

更完整的术语与约定见：`references/conventions.md`。

---

## 命名与ID

### 对象目录命名

所有需要稳定追踪的对象目录（如 change/plan/run）使用统一命名：

`{NNNNNN}_{type}_{slug}`

- `NNNNNN`：6位补零递增号（由脚本发号）
- `type`：`feat|fix|refactor|perf|docs|chore|security|test`
- `slug`：kebab-case（小写字母/数字/连字符）

### 稳定ID（建议）

文档头部建议保留稳定 ID，用于跨文件引用（即使目录/标题调整也不易断链）：

- `tasks/<name>/`（change/plan/runs）：`CHG-{NNNNNN}`
- `specs/`：`SPEC-{NNNNNN}`（可选；引用仍以 `domain/capability` 为主）

---

## 脚本

### 递增ID发号

使用 `scripts/sa_id.py` 生成递增号（默认写入 `superagents/.sa/registry.json`）：

```bash
python3 .codex/skills/superagents/scripts/sa_id.py
python3 .codex/skills/superagents/scripts/sa_id.py --type feat --slug add-release-automation
python3 .codex/skills/superagents/scripts/sa_id.py --dry-run --type fix --slug handle-empty-config
```

### 初始化 superagents 目录

在项目根目录创建 `superagents/` 结构与模板：

```bash
python3 .codex/skills/superagents/scripts/sa_init.py
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
```

`sa_init.py` 会初始化项目内的约定/工作流/评分文档：`superagents/.sa/wiki/*`。

### 新建 change + plan

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type feat --slug add-release-automation --title "Add release automation"
python3 .codex/skills/superagents/scripts/sa_index.py
python3 .codex/skills/superagents/scripts/sa_validate.py
```

### 评分缺口分析（自动追问清单）

对现有 `change.md/task.md` 做缺口分析，输出建议分数与追问问题（辅助把评分变成“系统”）：

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py --name 000123_feat_add-release-automation
python3 .codex/skills/superagents/scripts/sa_assess.py   # 扫描全部 changes
```

### 新建 spec（domain/capability）

```bash
python3 .codex/skills/superagents/scripts/sa_new_spec.py --domain payment --capability refund --title "Refund"
python3 .codex/skills/superagents/scripts/sa_index.py
```

### 编译机读索引（JSON）

将 `specs/tasks` 编译为 JSON（默认输出到 `superagents/.sa/wiki/catalog.generated.json`）：

```bash
python3 .codex/skills/superagents/scripts/sa_compile.py
python3 .codex/skills/superagents/scripts/sa_compile.py --check
```

### 一键检查（项目/CI入口）

统一检查入口（校验 + 索引 + 编译）：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

### 自检（doctor）

对当前项目的 `superagents/` 做环境与目录自检（不修改任何文件）：

```bash
python3 .codex/skills/superagents/scripts/sa_doctor.py
python3 .codex/skills/superagents/scripts/sa_doctor.py --json
```

### 迁移（migrate）

对旧文档补字段/补结构，并可选升级到推荐 `schema_version`：

```bash
python3 .codex/skills/superagents/scripts/sa_migrate.py --upgrade --dry-run
python3 .codex/skills/superagents/scripts/sa_migrate.py --upgrade
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

### 新建 run 记录

```bash
python3 .codex/skills/superagents/scripts/sa_new_run.py --name 000123_feat_add-release-automation
python3 .codex/skills/superagents/scripts/sa_index.py
```

### 归档（history）

将已完成对象归档到 `superagents/.sa/history/YYYY-MM/`（默认复制，安全）：

```bash
python3 .codex/skills/superagents/scripts/sa_archive.py --name 000123_feat_add-release-automation
```

---

## 工作流（建议）

superagents 的推荐闭环流程与质量门禁见：

- `references/workflows.md`
- `references/statuses.md`
- `references/scoring.md`

---

## 持续推进闭环（强制）

使用本 skill 时遵循“持续推进直到验证完成”的闭环：**不以“我写完代码了”作为结束条件**，而是以“验证通过 + 留痕完整 + 门禁通过”为结束条件。

### 执行循环（Loop）

1) **澄清与门禁**：信息不足或评分不达标（`clarity_score/readiness_score < 7`）时，必须先追问/补齐文档再推进状态
2) **计划与实施**：按 `tasks/*/plan/task.md` 执行；遇到阻塞写明原因与解除条件
3) **验证与留痕**：每次关键验证（单测/集成/回归/压测/人工验收）都新增 `tasks/<name>/runs/*.md` 记录结果与证据
4) **收口**：`tasks/<name>/runs` 至少 1 条 `status=success` → `plan=done` → `change=done` → `sa_validate` 通过 → 可选 `sa_archive`

### 收口标准（DoD，最小版）

- ✅ `sa_validate.py` 通过（结构/门禁/状态一致性）
- ✅ `tasks/<name>/plan/task.md`：`status=done`
- ✅ `tasks/<name>/change/change.md`：`status=done`
- ✅ `tasks/<name>/runs/`：至少 1 条 `status=success` 且包含验证证据位置
- ✅ 已生成/更新索引：`sa_index.py`

---

## 常见问题（FAQ）

**Q: 我不满意这套体系，怎么撤回？**  
A: 直接删除项目根目录下的 `superagents/`；本体系不要求修改其他目录（可选接入项在 `superagents/.sa/wiki/integration.md`）。

**Q: SSOT 到底是哪两个？**  
A: 只有 `superagents/specs/` 与 `superagents/tasks/*/change/`。

**Q: CI 怎么接入？**  
A: 直接跑 `python3 .codex/skills/superagents/scripts/sa_check.py`（详细见 `superagents/.sa/wiki/integration.md`）。
