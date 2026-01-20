#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sa_util import extract_frontmatter_value


TYPE_CHOICES = (
    "feat",
    "fix",
    "refactor",
    "perf",
    "docs",
    "chore",
    "security",
    "test",
)

KIND_CHOICES = (
    "chg",
    "spec",
)

KIND_PREFIX = {
    "chg": "CHG",
    "spec": "SPEC",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEADING_ID_RE = re.compile(r"^(?P<id>\d+)_")
STABLE_ID_RE = re.compile(r"^(?P<prefix>CHG|SPEC)-(?P<id>\d+)$")


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, path)


@dataclass(frozen=True)
class LockHandle:
    fd: int
    lock_path: Path


def acquire_lock(lock_path: Path, timeout_sec: float) -> LockHandle:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            return LockHandle(fd=fd, lock_path=lock_path)
        except FileExistsError:
            if time.time() - start >= timeout_sec:
                raise TimeoutError(f"获取锁超时: {lock_path}")
            time.sleep(0.1)


def release_lock(handle: LockHandle) -> None:
    try:
        os.close(handle.fd)
    finally:
        try:
            os.unlink(handle.lock_path)
        except FileNotFoundError:
            return


def read_registry(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"registry 格式错误（需为JSON对象）: {path}")
    schema_version = int(data.get("schema_version", 1) or 1)
    data["schema_version"] = schema_version
    if schema_version == 1:
        if "last_id" not in data:
            raise ValueError(f"registry 缺少 last_id: {path}")
        try:
            data["last_id"] = int(data["last_id"])
        except (TypeError, ValueError):
            raise ValueError(f"registry.last_id 不是整数: {path}")
        return data
    if schema_version >= 2:
        counters = data.get("counters")
        if counters is None:
            counters = {}
        if not isinstance(counters, dict):
            raise ValueError(f"registry.counters 需为对象: {path}")
        normalized: dict[str, int] = {}
        for k, v in counters.items():
            if not isinstance(k, str):
                continue
            try:
                normalized[k] = int(v)
            except (TypeError, ValueError):
                raise ValueError(f"registry.counters[{k}] 不是整数: {path}")
        data["counters"] = normalized
        return data
    raise ValueError(f"registry.schema_version 非法: {path}")


def allocate_next_id(
    *,
    root: Path,
    registry_relpath: str,
    pad: int,
    timeout_sec: float,
    dry_run: bool,
    scan: bool,
    kind: str,
) -> dict:
    registry_path = root / registry_relpath
    lock_path = registry_path.with_name(registry_path.name + ".lock")

    handle = acquire_lock(lock_path, timeout_sec=timeout_sec)
    try:
        if kind not in KIND_CHOICES:
            raise ValueError(f"kind 不在枚举中: {kind!r}（允许: {KIND_CHOICES}）")
        prefix = KIND_PREFIX[kind]

        registry = read_registry(registry_path)
        superagents_dir = (root / Path(registry_relpath).parent).resolve()
        scanned = scan_max_ids(superagents_dir) if scan else {"chg": 0, "spec": 0}

        # 兼容：schema_version=1 自动升级为 schema_version=2（分号）
        if registry is None:
            counters = {
                "chg": int(scanned.get("chg", 0)),
                "spec": int(scanned.get("spec", 0)),
            }
            registry = {"schema_version": 2, "counters": counters, "updated_at": utc_now_iso()}
        elif int(registry.get("schema_version", 1)) == 1:
            last_id = int(registry.get("last_id", 0))
            counters = {
                "chg": max(int(scanned.get("chg", 0)), last_id),
                "spec": int(scanned.get("spec", 0)),
            }
            registry = {"schema_version": 2, "counters": counters, "updated_at": utc_now_iso()}
        else:
            counters = dict(registry.get("counters") or {})
            counters["chg"] = max(int(counters.get("chg", 0)), int(scanned.get("chg", 0)))
            counters["spec"] = max(int(counters.get("spec", 0)), int(scanned.get("spec", 0)))
            registry["schema_version"] = int(registry.get("schema_version", 2) or 2)
            registry["counters"] = counters

        counters = registry["counters"]
        current = int(counters.get(kind, 0))
        next_id = current + 1
        padded_id = str(next_id).zfill(pad)
        stable_id = f"{prefix}-{padded_id}"

        if not dry_run:
            counters[kind] = next_id
            registry["updated_at"] = utc_now_iso()
            write_json_atomic(registry_path, registry)

        return {
            "id": next_id,
            "padded_id": padded_id,
            "stable_id": stable_id,
            "kind": kind,
            "registry_path": registry_path,
            "dry_run": bool(dry_run),
        }
    finally:
        release_lock(handle)


def scan_max_ids(superagents_dir: Path) -> dict[str, int]:
    max_chg = 0
    max_spec = 0

    def bump_chg(name: str) -> None:
        nonlocal max_chg
        m = LEADING_ID_RE.match(name)
        if not m:
            return
        try:
            value = int(m.group("id"))
        except ValueError:
            return
        if value > max_chg:
            max_chg = value

    tasks_dir = superagents_dir / "tasks"
    if tasks_dir.exists():
        for child in tasks_dir.iterdir():
            if not child.is_dir():
                continue
            bump_chg(child.name)

    # .sa/history/YYYY-MM/<name>（归档默认写在月目录下）
    history_dir = superagents_dir / ".sa" / "history"
    if history_dir.exists():
        for month in history_dir.iterdir():
            if not month.is_dir():
                continue
            for task_dir in month.iterdir():
                if not task_dir.is_dir():
                    continue
                bump_chg(task_dir.name)

    specs_dir = superagents_dir / "specs"
    if specs_dir.exists():
        for spec_md in specs_dir.glob("*/*/spec.md"):
            text = spec_md.read_text(encoding="utf-8")
            doc_id = extract_frontmatter_value(text, "id") or ""
            m = STABLE_ID_RE.match(doc_id)
            if not m:
                continue
            if m.group("prefix") not in {"SPEC"}:
                continue
            try:
                value = int(m.group("id"))
            except ValueError:
                continue
            if value > max_spec:
                max_spec = value

    return {"chg": max_chg, "spec": max_spec}


def scan_max_id(superagents_dir: Path) -> int:
    # legacy wrapper: 返回最大 chg 序号（与旧 last_id 更接近）
    return int(scan_max_ids(superagents_dir).get("chg", 0))


def normalize_slug(slug: str) -> str:
    slug = slug.strip()
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"slug 不合法（需kebab-case，小写字母/数字/连字符）: {slug!r}")
    return slug


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="sa_id.py",
        description="superagents 递增ID发号器（并发安全；按 kind 分号维护 superagents/.sa/registry.json）",
    )
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument(
        "--registry",
        default=os.path.join("superagents", ".sa", "registry.json"),
        help="registry 路径（相对 root；默认：superagents/.sa/registry.json）",
    )
    p.add_argument(
        "--kind",
        default="chg",
        choices=KIND_CHOICES,
        help="发号类型（chg=tasks(change/plan/runs)；spec=specs；默认：chg）",
    )
    p.add_argument("--pad", type=int, default=6, help="ID补零宽度（默认：6）")
    p.add_argument("--timeout", type=float, default=10.0, help="获取锁超时秒数（默认：10）")
    p.add_argument("--dry-run", action="store_true", help="仅计算并输出，不写入 registry")
    p.add_argument("--scan", action="store_true", help="registry 缺失时扫描已有目录推断最大ID（默认开启）")
    p.add_argument("--no-scan", action="store_true", help="registry 缺失时不扫描（从0开始）")
    p.add_argument("--type", choices=TYPE_CHOICES, help="改动类型（用于输出 name）")
    p.add_argument("--slug", help="kebab-case slug（用于输出 name）")
    p.add_argument("--json", action="store_true", help="输出 JSON（包含 padded_id / stable_id / name 等字段）")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    root = Path(args.root).resolve()

    scan = True
    if args.no_scan:
        scan = False
    if args.scan:
        scan = True

    if args.pad <= 0:
        raise ValueError("--pad 必须为正整数")

    if (args.type is None) != (args.slug is None):
        raise ValueError("--type 与 --slug 必须同时提供，或同时省略")
    if args.kind != "chg" and (args.type is not None or args.slug is not None):
        raise ValueError("--kind!=chg 时不允许使用 --type/--slug（仅 tasks 需要 name）")

    slug: Optional[str] = None
    if args.slug is not None:
        slug = normalize_slug(args.slug)

    allocation = allocate_next_id(
        root=root,
        registry_relpath=args.registry,
        pad=args.pad,
        timeout_sec=args.timeout,
        dry_run=bool(args.dry_run),
        scan=bool(scan),
        kind=str(args.kind),
    )
    padded_id = allocation["padded_id"]
    stable_id = allocation["stable_id"]

    name: Optional[str] = None
    if args.type is not None and slug is not None:
        name = f"{padded_id}_{args.type}_{slug}"

    if args.json:
        out = {
            "id": allocation["id"],
            "padded_id": padded_id,
            "stable_id": stable_id,
            "kind": args.kind,
            "type": args.type,
            "slug": slug,
            "name": name,
            "registry": os.path.relpath(str(allocation["registry_path"]), str(root)),
            "dry_run": bool(allocation["dry_run"]),
        }
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(name or padded_id)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ValueError, TimeoutError) as e:
        print(f"[sa_id] 错误: {e}", file=sys.stderr)
        raise SystemExit(2)
