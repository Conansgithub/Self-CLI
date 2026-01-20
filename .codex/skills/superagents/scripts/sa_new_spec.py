#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

import sa_id
import sa_index
from sa_util import now_date, render_template, skill_root_from_script, write_text_atomic


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_new_spec.py", description="创建新的 superagents spec 骨架（domain/capability）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--domain", required=True, help="domain（建议小写）")
    p.add_argument("--capability", required=True, help="capability（建议kebab-case）")
    p.add_argument("--title", help="标题（默认：domain/capability）")
    p.add_argument("--owner", default="@owner", help="owner（默认：@owner）")
    p.add_argument("--force", action="store_true", help="覆盖已存在 spec.md（谨慎）")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    p.add_argument("--no-index", action="store_true", help="不自动刷新 wiki 索引")
    return p.parse_args(argv)


def ensure_exists(dir_path: Path) -> None:
    if not dir_path.exists():
        raise FileNotFoundError(f"未找到 {dir_path}，请先运行 sa_init.py 初始化 superagents/")


def load_template(superagents_dir: Path, template_name: str, asset_name: str) -> str:
    project_tpl = superagents_dir / ".sa" / "templates" / template_name
    if project_tpl.exists():
        return project_tpl.read_text(encoding="utf-8")
    skill_root = skill_root_from_script(Path(__file__))
    return (skill_root / "assets" / "templates" / asset_name).read_text(encoding="utf-8")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    ensure_exists(superagents_dir)

    allocation = sa_id.allocate_next_id(
        root=root,
        registry_relpath=os.path.join(args.dir, ".sa", "registry.json"),
        pad=6,
        timeout_sec=10.0,
        dry_run=bool(args.dry_run),
        scan=True,
        kind="spec",
    )
    stable_id = allocation["stable_id"]

    domain = args.domain.strip()
    capability = args.capability.strip()
    title = args.title or f"{domain}/{capability}"

    spec_dir = superagents_dir / "specs" / domain / capability
    spec_md = spec_dir / "spec.md"
    if spec_md.exists() and not args.force:
        raise FileExistsError(f"spec.md 已存在: {spec_md}")

    values = {
        "ID": stable_id,
        "TITLE": title,
        "DOMAIN": domain,
        "CAPABILITY": capability,
        "OWNER": args.owner,
        "DATE": now_date(),
    }
    tpl = load_template(superagents_dir, "spec.md", "spec.md.tpl")
    content = render_template(tpl, values)

    if not args.dry_run:
        spec_dir.mkdir(parents=True, exist_ok=True)
        write_text_atomic(spec_md, content)
        if not args.no_index:
            sa_index.main(["--root", str(root), "--dir", args.dir, "--quiet"])

    result = {
        "stable_id": stable_id,
        "spec": os.path.relpath(str(spec_md), str(root)),
        "dry_run": bool(args.dry_run),
    }
    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["spec"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
