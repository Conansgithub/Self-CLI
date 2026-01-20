#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

import sa_id
import sa_index
from sa_util import (
    now_date,
    now_datetime,
    render_template,
    sa_change_dir,
    sa_plan_dir,
    sa_runs_dir,
    skill_root_from_script,
    write_text_atomic,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_new.py", description="创建新的 superagents task（change + plan，可选 runs）骨架")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--type", required=True, choices=sa_id.TYPE_CHOICES, help="改动类型")
    p.add_argument("--slug", required=True, help="kebab-case slug")
    p.add_argument("--title", help="标题（默认：由 slug 自动生成）")
    p.add_argument("--owner", default="@owner", help="owner（默认：@owner）")
    p.add_argument("--no-run", action="store_true", help="不创建 tasks/<name>/runs/ 目录")
    p.add_argument("--force", action="store_true", help="覆盖已存在文件（谨慎）")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    p.add_argument("--no-index", action="store_true", help="不自动刷新 wiki 索引")
    return p.parse_args(argv)


def load_template(superagents_dir: Path, template_name: str, asset_name: str) -> str:
    project_tpl = superagents_dir / ".sa" / "templates" / template_name
    if project_tpl.exists():
        return project_tpl.read_text(encoding="utf-8")
    skill_root = skill_root_from_script(Path(__file__))
    path = skill_root / "assets" / "templates" / asset_name
    return path.read_text(encoding="utf-8")


def ensure_exists(dir_path: Path) -> None:
    if not dir_path.exists():
        raise FileNotFoundError(f"未找到 {dir_path}，请先运行 sa_init.py 初始化 superagents/")


def write_doc(path: Path, content: str, *, force: bool, dry_run: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"文件已存在: {path}")
    if dry_run:
        return
    write_text_atomic(path, content)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    ensure_exists(superagents_dir)

    slug = sa_id.normalize_slug(args.slug)
    title = args.title or slug.replace("-", " ")

    allocation = sa_id.allocate_next_id(
        root=root,
        registry_relpath=os.path.join(args.dir, ".sa", "registry.json"),
        pad=6,
        timeout_sec=10.0,
        dry_run=bool(args.dry_run),
        scan=True,
        kind="chg",
    )
    padded_id = allocation["padded_id"]
    stable_id = allocation["stable_id"]
    name = f"{padded_id}_{args.type}_{slug}"

    change_dir = sa_change_dir(superagents_dir, name)
    plan_dir = sa_plan_dir(superagents_dir, name)
    run_dir = sa_runs_dir(superagents_dir, name)

    change_md = change_dir / "change.md"
    task_md = plan_dir / "task.md"

    values = {
        "ID": stable_id,
        "PADDED_ID": padded_id,
        "TYPE": args.type,
        "SLUG": slug,
        "NAME": name,
        "TITLE": title,
        "DATE": now_date(),
        "DATETIME": now_datetime(),
        "OWNER": args.owner,
    }

    if not args.dry_run:
        change_dir.mkdir(parents=True, exist_ok=True)
        plan_dir.mkdir(parents=True, exist_ok=True)
        if not args.no_run:
            run_dir.mkdir(parents=True, exist_ok=True)

    change_tpl = load_template(superagents_dir, "change.md", "change.md.tpl")
    task_tpl = load_template(superagents_dir, "task.md", "task.md.tpl")

    write_doc(change_md, render_template(change_tpl, values), force=bool(args.force), dry_run=bool(args.dry_run))
    write_doc(task_md, render_template(task_tpl, values), force=bool(args.force), dry_run=bool(args.dry_run))

    if not args.dry_run and not args.no_index:
        sa_index.main(["--root", str(root), "--dir", args.dir, "--quiet"])

    result = {
        "id": allocation["id"],
        "padded_id": padded_id,
        "stable_id": stable_id,
        "name": name,
        "change_dir": os.path.relpath(str(change_dir), str(root)),
        "plan_dir": os.path.relpath(str(plan_dir), str(root)),
        "run_dir": None if args.no_run else os.path.relpath(str(run_dir), str(root)),
        "dry_run": bool(args.dry_run),
    }

    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["name"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
