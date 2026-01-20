#!/usr/bin/env python3
from __future__ import annotations

import argparse

import sa_compile
import sa_index
import sa_validate


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_check.py", description="一键检查 superagents（validate + index + compile）")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--fix", action="store_true", help="自动更新索引与编译产物（写入 generated 文件）")
    p.add_argument("--quiet", action="store_true", help="静默模式（减少输出）")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.fix:
        index_args = ["--root", args.root, "--dir", args.dir]
        compile_args = ["--root", args.root, "--dir", args.dir]
        if args.quiet:
            index_args.append("--quiet")
            compile_args.append("--quiet")
        sa_index.main(index_args)
        sa_compile.main(compile_args)

    validate_rc = sa_validate.main(["--root", args.root, "--dir", args.dir])
    if validate_rc != 0:
        return validate_rc

    index_args = ["--root", args.root, "--dir", args.dir, "--check"]
    compile_args = ["--root", args.root, "--dir", args.dir, "--check"]
    if args.quiet:
        index_args.append("--quiet")
        compile_args.append("--quiet")
    index_rc = sa_index.main(index_args)
    compile_rc = sa_compile.main(compile_args)

    if index_rc != 0 or compile_rc != 0:
        if not args.quiet:
            print("检查未通过：generated 文件需要更新（可用 --fix 自动更新）")
        return 1

    if not args.quiet:
        print("检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
