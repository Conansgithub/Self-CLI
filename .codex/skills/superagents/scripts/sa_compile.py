#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import sa_id
from sa_util import extract_frontmatter_value, now_datetime, write_text_atomic


CHECKBOX_LINE_RE = re.compile(r"^\s*-\s*\[(?P<checked>[ xX])\]\s+(?P<rest>.+?)\s*$")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_compile.py", description="将 superagents/specs 等内容编译为可机读 JSON（generated）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--out", default=None, help="输出文件（默认：superagents/.sa/wiki/catalog.generated.json）")
    p.add_argument("--pretty", action="store_true", help="美化 JSON（缩进输出）")
    p.add_argument("--check", action="store_true", help="只检查是否需要更新（不写入）")
    p.add_argument("--quiet", action="store_true", help="静默模式（不输出提示文本）")
    return p.parse_args(argv)


def rel(root: Path, p: Path) -> str:
    return os.path.relpath(str(p), str(root))


def section_body(markdown: str, h2_title: str) -> str:
    lines = markdown.splitlines()
    heading = f"## {h2_title}"
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    out: list[str] = []
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


def h3_block(body: str, title: str) -> str:
    lines = body.splitlines()
    heading = f"### {title}"
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    out: list[str] = []
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith("### ") or line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


def parse_checkbox_items(block: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in block.splitlines():
        m = CHECKBOX_LINE_RE.match(line)
        if not m:
            continue
        rest = m.group("rest").strip()
        items.append(
            {
                "checked": m.group("checked").lower() == "x",
                "text": rest,
            }
        )
    return items


def extract_id(items: list[dict[str, Any]], prefix: str) -> None:
    pattern = re.compile(rf"\b{re.escape(prefix)}-(\d{{3}})\b")
    for item in items:
        m = pattern.search(item.get("text") or "")
        if m:
            item["id"] = f"{prefix}-{m.group(1)}"


def compile_specs(root: Path, superagents_dir: Path) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for spec_path in sorted((superagents_dir / "specs").glob("*/*/spec.md")):
        text = spec_path.read_text(encoding="utf-8")
        schema_version = extract_frontmatter_value(text, "schema_version") or ""
        title = extract_frontmatter_value(text, "title") or spec_path.parent.name
        status = extract_frontmatter_value(text, "status") or "unknown"
        domain = extract_frontmatter_value(text, "domain") or spec_path.parent.parent.name
        capability = extract_frontmatter_value(text, "capability") or spec_path.parent.name

        fr_body = section_body(text, "需求与规则（FR）")
        fr = []
        for level in ("MUST", "SHOULD", "MAY"):
            items = parse_checkbox_items(h3_block(fr_body, level))
            extract_id(items, "FR")
            fr.append({"level": level, "items": items})

        nfr_body = section_body(text, "非功能性需求（NFR）")
        nfr = []
        for cat in ("性能", "安全", "可靠性", "可观测性（日志/指标/告警）", "可维护性"):
            items = parse_checkbox_items(h3_block(nfr_body, cat))
            extract_id(items, "NFR")
            nfr.append({"category": cat, "items": items})

        ac_items = parse_checkbox_items(section_body(text, "验收标准（AC）"))
        extract_id(ac_items, "AC")

        specs.append(
            {
                "path": rel(root, spec_path),
                "id": extract_frontmatter_value(text, "id") or "",
                "schema_version": schema_version,
                "title": title,
                "status": status,
                "domain": domain,
                "capability": capability,
                "fr": fr,
                "nfr": nfr,
                "ac": ac_items,
                "created_at": extract_frontmatter_value(text, "created_at") or "",
                "updated_at": extract_frontmatter_value(text, "updated_at") or "",
            }
        )
    return specs


def compile_tasks(root: Path, superagents_dir: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    tasks_dir = superagents_dir / "tasks"
    if not tasks_dir.exists():
        return tasks

    def numeric_id(name: str) -> int:
        m = sa_id.LEADING_ID_RE.match(name)
        if not m:
            return 0
        try:
            return int(m.group("id"))
        except ValueError:
            return 0

    for task_dir in sorted([p for p in tasks_dir.iterdir() if p.is_dir()], key=lambda p: numeric_id(p.name)):
        if not sa_id.LEADING_ID_RE.match(task_dir.name):
            continue

        change_md = task_dir / "change" / "change.md"
        plan_md = task_dir / "plan" / "task.md"
        runs_dir = task_dir / "runs"

        change: dict[str, Any] = {"path": rel(root, change_md), "missing": True}
        if change_md.exists():
            text = change_md.read_text(encoding="utf-8")
            change = {
                "path": rel(root, change_md),
                "id": extract_frontmatter_value(text, "id") or "",
                "schema_version": extract_frontmatter_value(text, "schema_version") or "",
                "title": extract_frontmatter_value(text, "title") or task_dir.name,
                "status": extract_frontmatter_value(text, "status") or "unknown",
                "type": extract_frontmatter_value(text, "type") or "",
                "slug": extract_frontmatter_value(text, "slug") or "",
                "spec_refs": extract_frontmatter_value(text, "spec_refs") or "",
                "risk_level": extract_frontmatter_value(text, "risk_level") or "",
                "risk_flags": extract_frontmatter_value(text, "risk_flags") or "",
                "clarity_score": extract_frontmatter_value(text, "clarity_score") or "",
                "created_at": extract_frontmatter_value(text, "created_at") or "",
                "updated_at": extract_frontmatter_value(text, "updated_at") or "",
            }

        plan: dict[str, Any] = {"path": rel(root, plan_md), "missing": True}
        if plan_md.exists():
            text = plan_md.read_text(encoding="utf-8")
            plan = {
                "path": rel(root, plan_md),
                "id": extract_frontmatter_value(text, "id") or "",
                "schema_version": extract_frontmatter_value(text, "schema_version") or "",
                "title": extract_frontmatter_value(text, "title") or task_dir.name,
                "status": extract_frontmatter_value(text, "status") or "unknown",
                "spec_refs": extract_frontmatter_value(text, "spec_refs") or "",
                "risk_level": extract_frontmatter_value(text, "risk_level") or "",
                "risk_flags": extract_frontmatter_value(text, "risk_flags") or "",
                "readiness_score": extract_frontmatter_value(text, "readiness_score") or "",
                "created_at": extract_frontmatter_value(text, "created_at") or "",
                "updated_at": extract_frontmatter_value(text, "updated_at") or "",
            }

        run_files = sorted([p for p in runs_dir.glob("*.md") if p.is_file()]) if runs_dir.exists() else []
        latest: dict[str, Any] = {"status": "unknown", "path": ""}
        if run_files:
            latest_file = run_files[-1]
            text = latest_file.read_text(encoding="utf-8")
            latest = {
                "path": rel(root, latest_file),
                "id": extract_frontmatter_value(text, "id") or "",
                "schema_version": extract_frontmatter_value(text, "schema_version") or "",
                "title": extract_frontmatter_value(text, "title") or task_dir.name,
                "status": extract_frontmatter_value(text, "status") or "unknown",
                "revision": extract_frontmatter_value(text, "revision") or "",
                "spec_refs": extract_frontmatter_value(text, "spec_refs") or "",
                "code_refs": extract_frontmatter_value(text, "code_refs") or "",
                "risk_level": extract_frontmatter_value(text, "risk_level") or "",
                "change_name": extract_frontmatter_value(text, "change_name") or "",
                "plan_name": extract_frontmatter_value(text, "plan_name") or "",
                "started_at": extract_frontmatter_value(text, "started_at") or "",
                "finished_at": extract_frontmatter_value(text, "finished_at") or "",
                "created_at": extract_frontmatter_value(text, "created_at") or "",
                "updated_at": extract_frontmatter_value(text, "updated_at") or "",
            }

        tasks.append(
            {
                "name": task_dir.name,
                "path": rel(root, task_dir),
                "change": change,
                "plan": plan,
                "runs": {
                    "path": rel(root, runs_dir),
                    "count": len(run_files),
                    "latest": latest,
                },
            }
        )

    return tasks


def write_if_changed(path: Path, content: str, *, check: bool) -> bool:
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if old == content:
            return False
    if check:
        return True
    write_text_atomic(path, content)
    return True


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    if not superagents_dir.exists():
        raise FileNotFoundError(f"未找到 {superagents_dir}，请先运行 sa_init.py 初始化 superagents/")

    out_path = Path(args.out) if args.out else Path(args.dir) / ".sa" / "wiki" / "catalog.generated.json"
    out_path = (root / out_path).resolve()

    payload = {
        "schema_version": 2,
        "generated_at": now_datetime(),
        "specs": compile_specs(root, superagents_dir),
        "tasks": compile_tasks(root, superagents_dir),
    }

    content = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=False) + "\n"
    changed = write_if_changed(out_path, content, check=bool(args.check))

    if args.check and changed:
        if not args.quiet:
            print("编译产物需要更新")
        return 1
    if not args.quiet:
        print("编译产物已更新" if changed else "编译产物无需更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
