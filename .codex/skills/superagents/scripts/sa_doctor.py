#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import sa_id


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_doctor.py", description="自检 superagents 环境与目录（不修改任何文件）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    return p.parse_args(argv)


def rel(root: Path, p: Path) -> str:
    return os.path.relpath(str(p), str(root))


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir

    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    infos.append(f"python={py_ver}")
    if sys.version_info < (3, 8):
        warnings.append("Python 版本偏旧（建议 3.9+），可能影响部分语法/工具链兼容性")

    if not superagents_dir.exists():
        errors.append(f"未找到 {rel(root, superagents_dir)}（请先运行 sa_init.py）")
    else:
        required_dirs = ("specs", "tasks", ".sa", ".sa/wiki", ".sa/templates", ".sa/history")
        for d in required_dirs:
            p = superagents_dir / Path(d)
            if not p.exists():
                errors.append(f"缺少目录: {rel(root, p)}")

        registry_path = superagents_dir / ".sa" / "registry.json"
        registry = None
        if not registry_path.exists():
            warnings.append(f"缺少 registry: {rel(root, registry_path)}（sa_new/sa_new_spec 会自动创建，但建议先 sa_init）")
        else:
            try:
                registry = sa_id.read_registry(registry_path)
            except Exception as e:
                errors.append(f"registry.json 无法解析或字段非法：{rel(root, registry_path)}: {e}")

        if registry is not None:
            scanned = sa_id.scan_max_ids(superagents_dir)
            infos.append(f"scanned_chg_max_id={int(scanned.get('chg', 0))}")
            infos.append(f"scanned_spec_max_id={int(scanned.get('spec', 0))}")

            schema_version = int(registry.get("schema_version", 1) or 1)
            infos.append(f"registry_schema_version={schema_version}")

            if schema_version == 1:
                last_id = int(registry.get("last_id", 0))
                infos.append(f"registry_last_id={last_id}")
                warnings.append("registry.schema_version=1（旧格式）；下次写入时会自动升级为分号 counters 格式")
                if int(scanned.get("chg", 0)) > last_id:
                    errors.append(
                        f"registry.last_id({last_id}) 小于目录扫描最大ID({int(scanned.get('chg', 0))})，可能导致ID冲突（建议手动提升 last_id 或删除 registry 让工具重建）"
                    )
            else:
                counters = registry.get("counters") or {}
                chg_last = int(counters.get("chg", 0))
                spec_last = int(counters.get("spec", 0))
                infos.append(f"registry_chg_last_id={chg_last}")
                infos.append(f"registry_spec_last_id={spec_last}")
                if int(scanned.get("chg", 0)) > chg_last:
                    errors.append(
                        f"registry.counters.chg({chg_last}) 小于目录扫描最大ID({int(scanned.get('chg', 0))})，可能导致ID冲突（建议提升 counters.chg 或删除 registry 让工具重建）"
                    )
                if int(scanned.get("spec", 0)) > spec_last:
                    errors.append(
                        f"registry.counters.spec({spec_last}) 小于 spec 扫描最大ID({int(scanned.get('spec', 0))})，可能导致ID冲突（建议提升 counters.spec 或删除 registry 让工具重建）"
                    )

        templates = ("spec.md", "change.md", "task.md", "run.md")
        for t in templates:
            p = superagents_dir / ".sa" / "templates" / t
            if not p.exists():
                warnings.append(f"缺少模板: {rel(root, p)}（建议 sa_init --force 重新拷贝模板）")

        wiki_files = (
            "index.md",
            "conventions.md",
            "workflows.md",
            "statuses.md",
            "scoring.md",
            "risk.md",
            "schema-versions.md",
            "version-history.md",
            "integration.md",
            "troubleshooting.md",
        )
        for w in wiki_files:
            p = superagents_dir / ".sa" / "wiki" / w
            if not p.exists():
                warnings.append(f"缺少 wiki 文件: {rel(root, p)}（建议 sa_init --force）")

        generated = (
            "specs-index.generated.md",
            "tasks-index.generated.md",
            "catalog.generated.json",
        )
        for g in generated:
            p = superagents_dir / ".sa" / "wiki" / g
            if not p.exists():
                warnings.append(f"缺少 generated: {rel(root, p)}（建议先运行 sa_check.py --fix）")

    result = {
        "root": str(root),
        "dir": args.dir,
        "infos": infos,
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for i in infos:
            print(f"[info] {i}")
        for w in warnings:
            print(f"[warn] {w}")
        for e in errors:
            print(f"[error] {e}")
        print("OK" if not errors else "NOT OK")

    if errors:
        return 2
    if warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
