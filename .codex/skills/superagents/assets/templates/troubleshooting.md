# superagents Troubleshooting（v1）

本文件用于把 `sa_validate.py / sa_check.py` 的常见报错转成可操作的修复步骤。

## 先跑这 3 条（80% 问题可解决）

```bash
python3 .codex/skills/superagents/scripts/sa_assess.py
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```

如果仍失败，再按下文逐条定位。

---

## 1) sa_check 提示 generated 需要更新

现象：
- 输出类似：`generated 文件需要更新（可用 --fix 自动更新）`

原因：
- 你修改了 `specs/tasks`，但没刷新 `.sa/wiki/*generated*` 与 `catalog.generated.json`

修复：
```bash
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

---

## 2) 缺少 superagents 目录或子目录

现象：
- `sa_validate` 报：`缺少目录: superagents/...`

原因：
- 没初始化，或目录被误删

修复：
```bash
python3 .codex/skills/superagents/scripts/sa_init.py
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

---

## 3) 目录命名不合法（NNNNNN_type_slug）

现象：
- `tasks 目录命名不合法` 等

原因：
- 目录名不符合 `{NNNNNN}_{type}_{slug}`（6位补零递增号 + 类型 + kebab-case）

修复：
- 建议用脚本创建：`sa_new.py`（不要手动起目录名）
- 若已手动创建：重命名目录并确保 `id/type/slug` 与目录一致

---

## 4) spec_refs 相关报错（追溯链缺失）

现象：
- `spec_refs 为空（追溯链缺失）`
- `spec_refs 条目格式不合法（需 domain/capability）`
- `spec_refs 引用的 spec 不存在`

原因：
- `spec_refs` 未填写，或写法不对，或引用的 spec 文件不存在

修复：
1) 先创建/补齐 spec（建议 draft）：
```bash
python3 .codex/skills/superagents/scripts/sa_new_spec.py --domain <domain> --capability <capability> --title "<title>"
```
2) 在 `change.md/task.md` 中填：
```yaml
spec_refs: "<domain>/<capability>"
```

---

## 5) 评分门禁（clarity/readiness < 7）

现象：
- `change.status=approved|in_progress|done 但 clarity_score<7`
- `plan.status=in_progress|done 但 readiness_score<7`

原因：
- 状态推进过快，文档质量不足

修复：
- 先用 `sa_assess.py` 看缺口与追问清单
- 补齐内容并提高分数，或把状态回退到 `draft/review/planned`

---

## 6) plan=done 但 runs 证据链不完整

现象：
- `plan=done 但缺少 runs 记录`
- `plan=done 但不存在 success run`

原因：
- 你把 plan 收口了，但没有写验证记录或没有成功验证

修复：
```bash
python3 .codex/skills/superagents/scripts/sa_new_run.py --name <NNNNNN_type_slug>
```
并在 run 中：
- 填 `status: success`
- 填 `revision`（或 `code_refs`）
- 填 “证据（日志/截图/命令输出）”

---

## 7) run=success 但无法定位代码版本

现象：
- `run.status=success 但 revision/code_refs 均为空`

原因：
- run 缺少代码定位信息

修复：
- 在 run frontmatter 中填一个即可：
  - `revision: <git sha/tag>`
  - 或 `code_refs: "path:line, path:line"`

---

## 8) 高风险门禁（risk_level=high/critical）

现象：
- `risk_level=high|critical 但 发布/灰度计划/兼容性与迁移 未明确`
- `risk_level=high|critical 且 run=success，但证据段为空`

修复：
- 在 `change.md`：
  - `发布/灰度计划（如适用）`、`兼容性/迁移`：明确写“做什么/不做什么/为什么”
- 在 `run.md`：
  - “证据（日志/截图/命令输出）”补齐

---

## 9) Spec 门禁（active 但 AC/FR/NFR 不满足）

现象：
- `spec.status=active 但 AC 为空`
- `spec.schema_version>=2 且 active，但存在未编号 AC 条目`
- `spec.schema_version>=3 且 active，但存在未编号 FR/NFR 条目`

修复：
- AC：使用 `AC-001` 编号且不重复
- FR：使用 `FR-001` 编号且不重复
- NFR：使用 `NFR-001` 编号且不重复

---

## 10) Python 缓存权限问题（macOS 常见）

现象：
- `py_compile` 报 `PermissionError` 指向 `~/Library/Caches/...`

修复（推荐）：
```bash
PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile .codex/skills/superagents/scripts/*.py
```
