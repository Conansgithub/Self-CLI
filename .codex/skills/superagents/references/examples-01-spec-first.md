# 示例 01：Spec-first（先写规范再做变更）


目标：用最短路径走通 “Spec → Change/Plan → Run → Gate”。

## 前置条件

- 在项目根目录执行
- 已可运行 `python3 .codex/skills/superagents/scripts/...`

## 步骤

1) 初始化：

```bash
python3 .codex/skills/superagents/scripts/sa_init.py
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

2) 创建 spec：

```bash
python3 .codex/skills/superagents/scripts/sa_new_spec.py --domain payment --capability refund --title "Refund"
python3 .codex/skills/superagents/scripts/sa_check.py --fix
```

3) 创建 change + plan：

```bash
python3 .codex/skills/superagents/scripts/sa_new.py --type feat --slug refund-v2 --title "Refund v2"
python3 .codex/skills/superagents/scripts/sa_assess.py --name 000001_feat_refund-v2
```

4) 手动补齐门禁关键字段（最少）：

- `superagents/tasks/000001_feat_refund-v2/change/change.md`
  - `spec_refs: "payment/refund"`
  - `risk_level: low`
  - `clarity_score: >=7` 后再把 `status` 推进到 `approved`
- `superagents/tasks/000001_feat_refund-v2/plan/task.md`
  - `spec_refs: "payment/refund"`
  - `risk_level: low`
  - `readiness_score: >=7` 后再把 `status` 推进到 `in_progress`

5) 创建 run 记录并写入证据：

```bash
python3 .codex/skills/superagents/scripts/sa_new_run.py --name 000001_feat_refund-v2
```

将 `superagents/tasks/000001_feat_refund-v2/runs/*.md` 的：
- `status` 置为 `success`
- `revision`（或 `code_refs`）填入可定位的代码版本
- “证据（日志/截图/命令输出）”段写明测试命令/输出位置/截图路径

6) 收口与检查：

```bash
python3 .codex/skills/superagents/scripts/sa_check.py --fix
python3 .codex/skills/superagents/scripts/sa_check.py
```

## 期望产物

- `superagents/specs/payment/refund/spec.md`
- `superagents/tasks/000001_feat_refund-v2/change/change.md`
- `superagents/tasks/000001_feat_refund-v2/plan/task.md`
- `superagents/tasks/000001_feat_refund-v2/runs/*.md`
- `superagents/.sa/wiki/*.generated.*`（索引与机读编译产物）

## 常见失败点

- `spec_refs` 为空或格式不对（必须是 `domain/capability`）
- `run.status=success` 但 `revision/code_refs` 为空（无法定位代码版本）
- `plan=done` 但没有 `success` 的 run
