#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import sa_id
from sa_util import sa_registry_path, skill_root_from_script, write_text_atomic


ASSET_MAP = {
    "project.md": ("project.md", "project.md"),
    "wiki-index.md": (".sa/wiki/index.md", "wiki/index.md"),
    "conventions.md": (".sa/wiki/conventions.md", "wiki/conventions.md"),
    "workflows.md": (".sa/wiki/workflows.md", "wiki/workflows.md"),
    "statuses.md": (".sa/wiki/statuses.md", "wiki/statuses.md"),
    "scoring.md": (".sa/wiki/scoring.md", "wiki/scoring.md"),
    "risk.md": (".sa/wiki/risk.md", "wiki/risk.md"),
    "integration.md": (".sa/wiki/integration.md", "wiki/integration.md"),
    "troubleshooting.md": (".sa/wiki/troubleshooting.md", "wiki/troubleshooting.md"),
    "schema-versions.md": (".sa/wiki/schema-versions.md", "wiki/schema-versions.md"),
    "version-history.md": (".sa/wiki/version-history.md", "wiki/version-history.md"),
    "history-index.md": (".sa/history/index.md", "history/index.md"),
    "spec.md.tpl": (".sa/templates/spec.md", "templates/spec.md.tpl"),
    "change.md.tpl": (".sa/templates/change.md", "templates/change.md.tpl"),
    "task.md.tpl": (".sa/templates/task.md", "templates/task.md.tpl"),
    "run.md.tpl": (".sa/templates/run.md", "templates/run.md.tpl"),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_init.py", description="初始化项目的 superagents/ 目录结构与模板")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--force", action="store_true", help="覆盖已存在的模板/索引文件")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    return p.parse_args(argv)


def ensure_dirs(superagents_dir: Path, dry_run: bool) -> None:
    for name in ("specs", "tasks", ".sa/wiki", ".sa/templates", ".sa/history"):
        path = superagents_dir / Path(name)
        if dry_run:
            continue
        path.mkdir(parents=True, exist_ok=True)


def ensure_registry(superagents_dir: Path, root: Path, dry_run: bool) -> None:
    registry_path = sa_registry_path(superagents_dir)
    if registry_path.exists():
        return
    scanned = sa_id.scan_max_ids(superagents_dir)
    registry = {
        "schema_version": 2,
        "counters": {"chg": int(scanned.get("chg", 0)), "spec": int(scanned.get("spec", 0))},
        "updated_at": sa_id.utc_now_iso(),
    }
    if dry_run:
        return
    sa_id.write_json_atomic(registry_path, registry)


def copy_assets(superagents_dir: Path, *, force: bool, dry_run: bool) -> list[Path]:
    skill_root = skill_root_from_script(Path(__file__))
    assets_dir = skill_root / "assets" / "templates"
    created: list[Path] = []

    for asset_name, (target_rel, _) in ASSET_MAP.items():
        source = assets_dir / asset_name
        target = superagents_dir / target_rel
        if target.exists() and not force:
            continue
        if not source.exists():
            raise FileNotFoundError(f"缺少内置模板: {source}")
        if dry_run:
            created.append(target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding="utf-8")
        write_text_atomic(target, content)
        created.append(target)

    return created


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir

    ensure_dirs(superagents_dir, dry_run=bool(args.dry_run))
    ensure_registry(superagents_dir, root, dry_run=bool(args.dry_run))
    created = copy_assets(superagents_dir, force=bool(args.force), dry_run=bool(args.dry_run))

    if not args.dry_run:
        os.chmod(superagents_dir, 0o755)

    if created:
        for p in created:
            print(os.path.relpath(str(p), str(root)))
    else:
        print("superagents 已初始化（无新增文件）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
