#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path

import sa_index
from sa_util import extract_frontmatter_value, now_date, write_text_atomic


MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_archive.py", description="归档已完成对象到 superagents/.sa/history/YYYY-MM/（默认复制，安全）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--name", required=True, help="对象名（如 000123_feat_example）")
    p.add_argument("--month", help="归档月份（YYYY-MM；默认：当前月份）")
    p.add_argument("--move", action="store_true", help="移动而非复制（会影响索引/引用，谨慎）")
    p.add_argument("--force", action="store_true", help="强制归档（即使 status 不是 done）")
    p.add_argument("--dry-run", action="store_true", help="只打印动作，不写入")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    p.add_argument("--no-index", action="store_true", help="move 模式下不刷新 wiki 索引")
    return p.parse_args(argv)


def copy_or_move_dir(src: Path, dst: Path, *, move: bool, dry_run: bool) -> None:
    if dry_run:
        return
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            if move:
                shutil.move(str(child), str(target))
            else:
                shutil.copytree(str(child), str(target), dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if move:
                shutil.move(str(child), str(target))
            else:
                shutil.copy2(str(child), str(target))


def append_history_index(history_index: Path, *, month: str, name: str, title: str, stable_id: str, dry_run: bool) -> None:
    link = f"{month}/{name}/change/change.md"
    line = f"- `{name}` ({stable_id}) - [{title}]({link})"
    if history_index.exists():
        old = history_index.read_text(encoding="utf-8")
        if re.search(rf"^-\s+`{re.escape(name)}`\b", old, flags=re.MULTILINE):
            return
        content = old.rstrip() + "\n" + line + "\n"
    else:
        content = "# superagents History\n\n" + line + "\n"
    if dry_run:
        return
    write_text_atomic(history_index, content)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    if not superagents_dir.exists():
        raise FileNotFoundError(f"未找到 {superagents_dir}，请先运行 sa_init.py 初始化 superagents/")

    name = args.name.strip()
    task_dir = superagents_dir / "tasks" / name

    change_md = task_dir / "change" / "change.md"
    task_md = task_dir / "plan" / "task.md"
    if not change_md.exists():
        raise FileNotFoundError(f"未找到 change.md: {change_md}")
    if not task_md.exists():
        raise FileNotFoundError(f"未找到 task.md: {task_md}")

    change_text = change_md.read_text(encoding="utf-8")
    task_text = task_md.read_text(encoding="utf-8")
    title = extract_frontmatter_value(change_text, "title") or name
    stable_id = extract_frontmatter_value(change_text, "id") or f"CHG-{name.split('_', 1)[0]}"
    change_status = extract_frontmatter_value(change_text, "status") or ""
    plan_status = extract_frontmatter_value(task_text, "status") or ""

    if not args.force and (change_status != "done" or plan_status != "done"):
        raise ValueError(f"仅允许归档已完成对象（change/plan status=done），当前为 change={change_status!r}, plan={plan_status!r}（可用 --force 强制）")

    month = (args.month or now_date()[:7]).strip()
    if not MONTH_RE.fullmatch(month):
        raise ValueError("--month 需为 YYYY-MM 格式")

    dest_dir = superagents_dir / ".sa" / "history" / month / name

    if not args.dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    copy_or_move_dir(task_dir, dest_dir, move=bool(args.move), dry_run=bool(args.dry_run))

    history_index = superagents_dir / ".sa" / "history" / "index.md"
    append_history_index(history_index, month=month, name=name, title=title, stable_id=stable_id, dry_run=bool(args.dry_run))

    # move 模式会改变 tasks 下的内容，需要刷新索引
    if args.move and (not args.dry_run) and (not args.no_index):
        sa_index.main(["--root", str(root), "--dir", args.dir, "--quiet"])

    result = {
        "name": name,
        "id": stable_id,
        "month": month,
        "archived": os.path.relpath(str(dest_dir), str(root)),
        "mode": "move" if args.move else "copy",
        "dry_run": bool(args.dry_run),
    }

    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["archived"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
