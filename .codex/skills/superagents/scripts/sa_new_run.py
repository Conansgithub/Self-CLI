#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

import sa_index
from sa_util import (
    extract_frontmatter_value,
    now_date,
    now_datetime,
    render_template,
    sa_change_md,
    sa_runs_dir,
    skill_root_from_script,
    write_text_atomic,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_new_run.py", description="为指定对象创建一条 runs 记录")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--name", required=True, help="对象名（如 000123_feat_example）")
    p.add_argument("--owner", default="@owner", help="owner（默认：@owner）")
    p.add_argument("--force", action="store_true", help="覆盖已存在同名 run 文件（谨慎）")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    p.add_argument("--no-index", action="store_true", help="不自动刷新 wiki 索引")
    return p.parse_args(argv)


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
    if not superagents_dir.exists():
        raise FileNotFoundError(f"未找到 {superagents_dir}，请先运行 sa_init.py 初始化 superagents/")

    name = args.name.strip()
    runs_dir = sa_runs_dir(superagents_dir, name)
    change_md = sa_change_md(superagents_dir, name)

    title = name
    stable_id = ""
    spec_refs = ""
    risk_level = "low"
    if change_md.exists():
        text = change_md.read_text(encoding="utf-8")
        title = extract_frontmatter_value(text, "title") or title
        stable_id = extract_frontmatter_value(text, "id") or stable_id
        spec_refs = extract_frontmatter_value(text, "spec_refs") or spec_refs
        risk_level = extract_frontmatter_value(text, "risk_level") or risk_level

    if not stable_id:
        # 兜底：从 name 前缀推断
        padded_id = name.split("_", 1)[0]
        if padded_id.isdigit() and len(padded_id) == 6:
            stable_id = f"CHG-{padded_id}"

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    run_md = runs_dir / f"{ts}.md"
    if run_md.exists() and not args.force:
        raise FileExistsError(f"run 文件已存在: {run_md}")

    values = {
        "ID": stable_id or "CHG-000000",
        "TITLE": title,
        "OWNER": args.owner,
        "NAME": name,
        "SPEC_REFS": spec_refs,
        "CODE_REFS": "",
        "RISK_LEVEL": risk_level,
        "DATE": now_date(),
        "DATETIME": now_datetime(),
    }
    tpl = load_template(superagents_dir, "run.md", "run.md.tpl")
    content = render_template(tpl, values)

    if not args.dry_run:
        runs_dir.mkdir(parents=True, exist_ok=True)
        write_text_atomic(run_md, content)
        if not args.no_index:
            sa_index.main(["--root", str(root), "--dir", args.dir, "--quiet"])

    result = {
        "run": os.path.relpath(str(run_md), str(root)),
        "dry_run": bool(args.dry_run),
    }
    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["run"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
