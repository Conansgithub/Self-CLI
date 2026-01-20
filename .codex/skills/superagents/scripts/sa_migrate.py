#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from sa_util import now_date, now_datetime, write_text_atomic


NAME_RE = re.compile(r"^(?P<padded_id>\d{6})_(?P<type>[a-z]+)_(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")

LATEST_SPEC_SCHEMA = 3
LATEST_CHANGE_SCHEMA = 2
LATEST_PLAN_SCHEMA = 2
LATEST_RUN_SCHEMA = 2

REQUIRED_SPEC_H2 = (
    "目标",
    "范围",
    "非目标",
    "背景与动机",
    "关键概念/术语",
    "用户故事 / 场景",
    "需求与规则（FR）",
    "非功能性需求（NFR）",
    "验收标准（AC）",
    "错误处理与边界条件",
    "开放问题",
)
REQUIRED_CHANGE_H2 = (
    "背景/动机",
    "范围（In/Out）",
    "头脑风暴（备选方案）",
    "评分与门禁（Clarity Score）",
    "变更内容",
    "影响分析",
    "验收标准变更",
    "回滚方案",
    "开放问题",
)
REQUIRED_PLAN_H2 = (
    "目标与成功标准",
    "就绪检查与评分（Readiness Score）",
    "任务清单",
    "实施步骤",
    "验证计划",
    "回滚计划",
    "风险与缓解",
)


@dataclass
class ChangeResult:
    path: str
    changed: bool
    reasons: list[str]


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_migrate.py", description="迁移/补齐 superagents 文档字段与结构（可选升级 schema_version）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    p.add_argument("--upgrade", action="store_true", help="升级 schema_version 到推荐版本（可能触发更严格门禁）")
    p.add_argument("--name", help="仅处理指定对象名（如 000123_feat_example；仅作用于 change/plan/run）")
    p.add_argument(
        "--only",
        default="all",
        choices=("all", "spec", "change", "plan", "run"),
        help="仅处理某一类文档（默认：all）",
    )
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    return p.parse_args(argv)


def rel(root: Path, p: Path) -> str:
    return os.path.relpath(str(p), str(root))


def split_frontmatter(text: str) -> tuple[list[str], list[str]] | tuple[None, None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :]
    return None, None


def join_frontmatter(frontmatter_lines: list[str], body_lines: list[str]) -> str:
    out: list[str] = ["---", *frontmatter_lines, "---", *body_lines]
    text = "\n".join(out).rstrip() + "\n"
    return text


def fm_index(frontmatter_lines: list[str], key: str) -> Optional[int]:
    prefix = f"{key}:"
    for i, line in enumerate(frontmatter_lines):
        if line.startswith(prefix):
            return i
    return None


def set_fm_scalar(
    frontmatter_lines: list[str],
    *,
    key: str,
    value: str,
    insert_before: tuple[str, ...] = ("owners", "links", "created_at", "updated_at"),
) -> bool:
    line = f"{key}: {value}"
    idx = fm_index(frontmatter_lines, key)
    if idx is not None:
        if frontmatter_lines[idx] == line:
            return False
        frontmatter_lines[idx] = line
        return True

    insert_at = len(frontmatter_lines)
    for anchor in insert_before:
        aidx = fm_index(frontmatter_lines, anchor)
        if aidx is not None:
            insert_at = min(insert_at, aidx)
    frontmatter_lines.insert(insert_at, line)
    return True


def ensure_fm_block(
    frontmatter_lines: list[str],
    *,
    key: str,
    block_lines: list[str],
    insert_before: tuple[str, ...] = ("created_at", "updated_at"),
) -> bool:
    if fm_index(frontmatter_lines, key) is not None:
        return False
    insert_at = len(frontmatter_lines)
    for anchor in insert_before:
        aidx = fm_index(frontmatter_lines, anchor)
        if aidx is not None:
            insert_at = min(insert_at, aidx)
    for i, line in enumerate(block_lines):
        frontmatter_lines.insert(insert_at + i, line)
    return True


def find_line(lines: list[str], needle: str) -> Optional[int]:
    for i, line in enumerate(lines):
        if line.strip() == needle:
            return i
    return None


def h2_range(lines: list[str], title: str) -> Optional[tuple[int, int]]:
    heading = f"## {title}"
    start = find_line(lines, heading)
    if start is None:
        return None
    body_start = start + 1
    end = len(lines)
    for i in range(body_start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return body_start, end


def ensure_h2(lines: list[str], title: str) -> bool:
    heading = f"## {title}"
    if find_line(lines, heading) is not None:
        return False
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(heading)
    lines.append("")
    return True


def ensure_h2s(lines: list[str], titles: Iterable[str]) -> bool:
    changed = False
    for t in titles:
        changed |= ensure_h2(lines, t)
    return changed


def ensure_h3_in_h2(lines: list[str], h2_title: str, h3_titles: Iterable[str]) -> bool:
    r = h2_range(lines, h2_title)
    if r is None:
        return False
    start, end = r
    changed = False
    existing = {lines[i].strip() for i in range(start, end) if lines[i].strip().startswith("### ")}
    insert_at = end
    for title in h3_titles:
        heading = f"### {title}"
        if heading in existing:
            continue
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, heading)
        lines.insert(insert_at + 2, "")
        insert_at += 3
        changed = True
    return changed


LIST_ITEM_RE = re.compile(r"^(?P<prefix>\s*-\s*)(?P<cb>\[[ xX]\]\s*)?(?P<rest>.+?)\s*$")


def collect_used_ids(lines: Iterable[str], prefix: str) -> set[int]:
    used: set[int] = set()
    pat = re.compile(rf"\b{re.escape(prefix)}-(\d{{3}})\b")
    for line in lines:
        m = pat.search(line)
        if not m:
            continue
        try:
            used.add(int(m.group(1)))
        except ValueError:
            continue
    return used


def assign_ids_in_h2(lines: list[str], h2_title: str, prefix: str) -> bool:
    r = h2_range(lines, h2_title)
    if r is None:
        return False
    start, end = r
    used = collect_used_ids(lines[start:end], prefix)
    changed = False
    next_id = 1

    def alloc() -> int:
        nonlocal next_id
        while next_id in used:
            next_id += 1
        used.add(next_id)
        out = next_id
        next_id += 1
        return out

    pat = re.compile(rf"\b{re.escape(prefix)}-\d{{3}}\b")
    for i in range(start, end):
        m = LIST_ITEM_RE.match(lines[i])
        if not m:
            continue
        if pat.search(lines[i]):
            continue
        n = alloc()
        rest = m.group("rest").strip()
        cb = m.group("cb") or ""
        lines[i] = f"{m.group('prefix')}{cb}{prefix}-{n:03d}: {rest}"
        changed = True
    return changed


def parse_schema(frontmatter_lines: list[str]) -> int:
    idx = fm_index(frontmatter_lines, "schema_version")
    if idx is None:
        return 0
    raw = frontmatter_lines[idx].split(":", 1)[1].strip().strip('"').strip("'")
    try:
        return int(raw)
    except ValueError:
        return 0


def migrate_spec(spec_md: Path, *, root: Path, upgrade: bool, dry_run: bool) -> ChangeResult:
    reasons: list[str] = []
    text = spec_md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None or body is None:
        return ChangeResult(path=rel(root, spec_md), changed=False, reasons=["缺少 frontmatter（跳过）"])

    changed = False
    domain = spec_md.parent.parent.name
    capability = spec_md.parent.name

    schema_before = parse_schema(fm)
    schema_target = LATEST_SPEC_SCHEMA if upgrade or schema_before == 0 else schema_before

    changed |= set_fm_scalar(fm, key="schema_version", value=str(schema_target))
    changed |= set_fm_scalar(fm, key="domain", value=f'"{domain}"')
    changed |= set_fm_scalar(fm, key="capability", value=f'"{capability}"')
    changed |= set_fm_scalar(fm, key="updated_at", value=f'"{now_date()}"')
    if fm_index(fm, "created_at") is None:
        changed |= set_fm_scalar(fm, key="created_at", value=f'"{now_date()}"')
    if fm_index(fm, "id") is None:
        changed |= set_fm_scalar(fm, key="id", value='"SPEC-000000"')
        reasons.append("补齐 id")
    if fm_index(fm, "title") is None:
        changed |= set_fm_scalar(fm, key="title", value=f'"{domain}/{capability}"')
        reasons.append("补齐 title")
    if fm_index(fm, "status") is None:
        changed |= set_fm_scalar(fm, key="status", value="draft")
        reasons.append("补齐 status")
    if fm_index(fm, "owners") is None:
        changed |= ensure_fm_block(fm, key="owners", block_lines=["owners:", '  - "@owner"'])
        reasons.append("补齐 owners")
    if fm_index(fm, "links") is None:
        changed |= ensure_fm_block(fm, key="links", block_lines=["links: []"])
        reasons.append("补齐 links")

    body_changed = False
    body_changed |= ensure_h2s(body, REQUIRED_SPEC_H2)

    if schema_target >= 2:
        body_changed |= ensure_h3_in_h2(body, "需求与规则（FR）", ("MUST", "SHOULD", "MAY"))
        body_changed |= ensure_h3_in_h2(
            body,
            "非功能性需求（NFR）",
            ("性能", "安全", "可靠性", "可观测性（日志/指标/告警）", "可维护性"),
        )
        body_changed |= assign_ids_in_h2(body, "验收标准（AC）", "AC")
    if schema_target >= 3:
        body_changed |= assign_ids_in_h2(body, "需求与规则（FR）", "FR")
        body_changed |= assign_ids_in_h2(body, "非功能性需求（NFR）", "NFR")

    changed |= body_changed
    if body_changed:
        reasons.append("补齐结构/编号")

    if not changed:
        return ChangeResult(path=rel(root, spec_md), changed=False, reasons=[])

    if not dry_run:
        write_text_atomic(spec_md, join_frontmatter(fm, body))
    return ChangeResult(path=rel(root, spec_md), changed=True, reasons=reasons or ["migrated"])


def migrate_change(change_md: Path, *, root: Path, name: str, upgrade: bool, dry_run: bool) -> ChangeResult:
    reasons: list[str] = []
    m = NAME_RE.match(name)
    if not m:
        return ChangeResult(path=rel(root, change_md), changed=False, reasons=["目录名不合法（跳过）"])

    text = change_md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None or body is None:
        return ChangeResult(path=rel(root, change_md), changed=False, reasons=["缺少 frontmatter（跳过）"])

    changed = False
    padded_id = m.group("padded_id")
    expected_id = f"CHG-{padded_id}"
    schema_before = parse_schema(fm)
    schema_target = LATEST_CHANGE_SCHEMA if upgrade or schema_before == 0 else schema_before

    changed |= set_fm_scalar(fm, key="id", value=f'"{expected_id}"')
    changed |= set_fm_scalar(fm, key="schema_version", value=str(schema_target))
    changed |= set_fm_scalar(fm, key="type", value=f'"{m.group("type")}"')
    changed |= set_fm_scalar(fm, key="slug", value=f'"{m.group("slug")}"')
    changed |= set_fm_scalar(fm, key="updated_at", value=f'"{now_date()}"')
    if fm_index(fm, "created_at") is None:
        changed |= set_fm_scalar(fm, key="created_at", value=f'"{now_date()}"')
        reasons.append("补齐 created_at")
    if fm_index(fm, "title") is None:
        changed |= set_fm_scalar(fm, key="title", value=f'"{m.group("slug").replace("-", " ")}"')
        reasons.append("补齐 title")
    if fm_index(fm, "status") is None:
        changed |= set_fm_scalar(fm, key="status", value="draft")
        reasons.append("补齐 status")
    if fm_index(fm, "clarity_score") is None:
        changed |= set_fm_scalar(fm, key="clarity_score", value="0")
        reasons.append("补齐 clarity_score")

    if schema_target >= 2:
        if fm_index(fm, "spec_refs") is None:
            changed |= set_fm_scalar(fm, key="spec_refs", value='""')
            reasons.append("补齐 spec_refs")
        if fm_index(fm, "risk_level") is None:
            changed |= set_fm_scalar(fm, key="risk_level", value="low")
            reasons.append("补齐 risk_level")
        if fm_index(fm, "risk_flags") is None:
            changed |= set_fm_scalar(fm, key="risk_flags", value='""')
            reasons.append("补齐 risk_flags")

    if fm_index(fm, "owners") is None:
        changed |= ensure_fm_block(fm, key="owners", block_lines=["owners:", '  - "@owner"'])
        reasons.append("补齐 owners")
    if fm_index(fm, "links") is None:
        changed |= ensure_fm_block(fm, key="links", block_lines=["links: []"])
        reasons.append("补齐 links")

    body_changed = ensure_h2s(body, REQUIRED_CHANGE_H2)
    changed |= body_changed
    if body_changed:
        reasons.append("补齐二级标题")

    if not changed:
        return ChangeResult(path=rel(root, change_md), changed=False, reasons=[])

    if not dry_run:
        write_text_atomic(change_md, join_frontmatter(fm, body))
    return ChangeResult(path=rel(root, change_md), changed=True, reasons=reasons or ["migrated"])


def migrate_plan(task_md: Path, *, root: Path, name: str, upgrade: bool, dry_run: bool) -> ChangeResult:
    reasons: list[str] = []
    m = NAME_RE.match(name)
    if not m:
        return ChangeResult(path=rel(root, task_md), changed=False, reasons=["目录名不合法（跳过）"])

    text = task_md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None or body is None:
        return ChangeResult(path=rel(root, task_md), changed=False, reasons=["缺少 frontmatter（跳过）"])

    changed = False
    padded_id = m.group("padded_id")
    expected_id = f"CHG-{padded_id}"
    schema_before = parse_schema(fm)
    schema_target = LATEST_PLAN_SCHEMA if upgrade or schema_before == 0 else schema_before

    changed |= set_fm_scalar(fm, key="id", value=f'"{expected_id}"')
    changed |= set_fm_scalar(fm, key="schema_version", value=str(schema_target))
    changed |= set_fm_scalar(fm, key="updated_at", value=f'"{now_date()}"')
    if fm_index(fm, "created_at") is None:
        changed |= set_fm_scalar(fm, key="created_at", value=f'"{now_date()}"')
        reasons.append("补齐 created_at")
    if fm_index(fm, "title") is None:
        changed |= set_fm_scalar(fm, key="title", value=f'"{m.group("slug").replace("-", " ")}"')
        reasons.append("补齐 title")
    if fm_index(fm, "status") is None:
        changed |= set_fm_scalar(fm, key="status", value="planned")
        reasons.append("补齐 status")
    if fm_index(fm, "readiness_score") is None:
        changed |= set_fm_scalar(fm, key="readiness_score", value="0")
        reasons.append("补齐 readiness_score")

    if schema_target >= 2:
        if fm_index(fm, "spec_refs") is None:
            changed |= set_fm_scalar(fm, key="spec_refs", value='""')
            reasons.append("补齐 spec_refs")
        if fm_index(fm, "risk_level") is None:
            changed |= set_fm_scalar(fm, key="risk_level", value="low")
            reasons.append("补齐 risk_level")
        if fm_index(fm, "risk_flags") is None:
            changed |= set_fm_scalar(fm, key="risk_flags", value='""')
            reasons.append("补齐 risk_flags")

    if fm_index(fm, "owners") is None:
        changed |= ensure_fm_block(fm, key="owners", block_lines=["owners:", '  - "@owner"'])
        reasons.append("补齐 owners")
    if fm_index(fm, "links") is None:
        changed |= ensure_fm_block(fm, key="links", block_lines=["links: []"])
        reasons.append("补齐 links")

    body_changed = ensure_h2s(body, REQUIRED_PLAN_H2)
    changed |= body_changed
    if body_changed:
        reasons.append("补齐二级标题")

    if not changed:
        return ChangeResult(path=rel(root, task_md), changed=False, reasons=[])

    if not dry_run:
        write_text_atomic(task_md, join_frontmatter(fm, body))
    return ChangeResult(path=rel(root, task_md), changed=True, reasons=reasons or ["migrated"])


def migrate_run(run_md: Path, *, root: Path, name: str, upgrade: bool, dry_run: bool) -> ChangeResult:
    reasons: list[str] = []
    m = NAME_RE.match(name)
    if not m:
        return ChangeResult(path=rel(root, run_md), changed=False, reasons=["目录名不合法（跳过）"])

    text = run_md.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    if fm is None or body is None:
        return ChangeResult(path=rel(root, run_md), changed=False, reasons=["缺少 frontmatter（跳过）"])

    changed = False
    padded_id = m.group("padded_id")
    expected_id = f"CHG-{padded_id}"
    schema_before = parse_schema(fm)
    schema_target = LATEST_RUN_SCHEMA if upgrade or schema_before == 0 else schema_before

    changed |= set_fm_scalar(fm, key="id", value=f'"{expected_id}"')
    changed |= set_fm_scalar(fm, key="schema_version", value=str(schema_target))
    changed |= set_fm_scalar(fm, key="change_name", value=f'"{name}"')
    changed |= set_fm_scalar(fm, key="plan_name", value=f'"{name}"')
    changed |= set_fm_scalar(fm, key="updated_at", value=f'"{now_date()}"')

    if fm_index(fm, "created_at") is None:
        changed |= set_fm_scalar(fm, key="created_at", value=f'"{now_date()}"')
        reasons.append("补齐 created_at")
    if fm_index(fm, "started_at") is None:
        changed |= set_fm_scalar(fm, key="started_at", value=f'"{now_datetime()}"')
        reasons.append("补齐 started_at")
    if fm_index(fm, "title") is None:
        changed |= set_fm_scalar(fm, key="title", value=f'"{name}"')
        reasons.append("补齐 title")
    if fm_index(fm, "status") is None:
        changed |= set_fm_scalar(fm, key="status", value="partial")
        reasons.append("补齐 status")

    if schema_target >= 2:
        if fm_index(fm, "spec_refs") is None:
            changed |= set_fm_scalar(fm, key="spec_refs", value='""')
            reasons.append("补齐 spec_refs")
        if fm_index(fm, "code_refs") is None:
            changed |= set_fm_scalar(fm, key="code_refs", value='""')
            reasons.append("补齐 code_refs")
        if fm_index(fm, "risk_level") is None:
            changed |= set_fm_scalar(fm, key="risk_level", value="low")
            reasons.append("补齐 risk_level")
        if fm_index(fm, "revision") is None:
            changed |= set_fm_scalar(fm, key="revision", value='""')
            reasons.append("补齐 revision")
        if fm_index(fm, "finished_at") is None:
            changed |= set_fm_scalar(fm, key="finished_at", value='""')
        if fm_index(fm, "env") is None:
            changed |= set_fm_scalar(fm, key="env", value='""')

    if fm_index(fm, "owners") is None:
        changed |= ensure_fm_block(fm, key="owners", block_lines=["owners:", '  - "@owner"'])
        reasons.append("补齐 owners")
    if fm_index(fm, "links") is None:
        changed |= ensure_fm_block(fm, key="links", block_lines=["links: []"])
        reasons.append("补齐 links")

    if not changed:
        return ChangeResult(path=rel(root, run_md), changed=False, reasons=[])

    if not dry_run:
        write_text_atomic(run_md, join_frontmatter(fm, body))
    return ChangeResult(path=rel(root, run_md), changed=True, reasons=reasons or ["migrated"])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    if not superagents_dir.exists():
        raise FileNotFoundError(f"未找到 {superagents_dir}，请先运行 sa_init.py 初始化 superagents/")

    changed: list[ChangeResult] = []
    skipped: list[ChangeResult] = []

    only = args.only
    do_all = only == "all"

    if do_all or only == "spec":
        specs_dir = superagents_dir / "specs"
        if specs_dir.exists():
            for spec_md in sorted(specs_dir.glob("*/*/spec.md")):
                r = migrate_spec(spec_md, root=root, upgrade=bool(args.upgrade), dry_run=bool(args.dry_run))
                (changed if r.changed else skipped).append(r)

    def wanted_name(n: str) -> bool:
        return True if not args.name else n == args.name

    if do_all or only == "change":
        tasks_dir = superagents_dir / "tasks"
        if tasks_dir.exists():
            for child in sorted([p for p in tasks_dir.iterdir() if p.is_dir()]):
                if not wanted_name(child.name):
                    continue
                change_md = child / "change" / "change.md"
                if not change_md.exists():
                    skipped.append(ChangeResult(path=rel(root, change_md), changed=False, reasons=["缺少 change.md（跳过）"]))
                    continue
                r = migrate_change(
                    change_md,
                    root=root,
                    name=child.name,
                    upgrade=bool(args.upgrade),
                    dry_run=bool(args.dry_run),
                )
                (changed if r.changed else skipped).append(r)

    if do_all or only == "plan":
        tasks_dir = superagents_dir / "tasks"
        if tasks_dir.exists():
            for child in sorted([p for p in tasks_dir.iterdir() if p.is_dir()]):
                if not wanted_name(child.name):
                    continue
                task_md = child / "plan" / "task.md"
                if not task_md.exists():
                    skipped.append(ChangeResult(path=rel(root, task_md), changed=False, reasons=["缺少 task.md（跳过）"]))
                    continue
                r = migrate_plan(
                    task_md,
                    root=root,
                    name=child.name,
                    upgrade=bool(args.upgrade),
                    dry_run=bool(args.dry_run),
                )
                (changed if r.changed else skipped).append(r)

    if do_all or only == "run":
        tasks_dir = superagents_dir / "tasks"
        if tasks_dir.exists():
            for child in sorted([p for p in tasks_dir.iterdir() if p.is_dir()]):
                if not wanted_name(child.name):
                    continue
                runs_dir = child / "runs"
                for run_md in sorted([p for p in runs_dir.glob("*.md") if p.is_file()]):
                    r = migrate_run(
                        run_md,
                        root=root,
                        name=child.name,
                        upgrade=bool(args.upgrade),
                        dry_run=bool(args.dry_run),
                    )
                    (changed if r.changed else skipped).append(r)

    result = {
        "dry_run": bool(args.dry_run),
        "upgrade": bool(args.upgrade),
        "only": args.only,
        "name": args.name,
        "changed": [{"path": r.path, "reasons": r.reasons} for r in changed if r.changed],
        "skipped": [{"path": r.path, "reasons": r.reasons} for r in skipped if not r.changed and r.reasons],
        "count_changed": len([r for r in changed if r.changed]),
    }

    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        prefix = "[dry-run] " if args.dry_run else ""
        if not changed:
            print("无变更")
        else:
            for r in changed:
                if not r.changed:
                    continue
                why = "; ".join(r.reasons) if r.reasons else "migrated"
                print(f"{prefix}{r.path} - {why}")
            print(f"{prefix}共更新 {result['count_changed']} 个文件")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
