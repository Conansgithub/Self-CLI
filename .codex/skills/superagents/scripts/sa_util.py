#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping, Optional


PLACEHOLDER_RE = re.compile(r"\{\{(?P<key>[A-Z0-9_]+)\}\}")
META_DIRNAME = ".sa"


def now_date() -> str:
    return datetime.now().date().isoformat()


def now_datetime() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def skill_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parent.parent


def sa_meta_dir(superagents_dir: Path) -> Path:
    return superagents_dir / META_DIRNAME


def sa_registry_path(superagents_dir: Path) -> Path:
    return sa_meta_dir(superagents_dir) / "registry.json"


def sa_wiki_dir(superagents_dir: Path) -> Path:
    return sa_meta_dir(superagents_dir) / "wiki"


def sa_templates_dir(superagents_dir: Path) -> Path:
    return sa_meta_dir(superagents_dir) / "templates"


def sa_history_dir(superagents_dir: Path) -> Path:
    return sa_meta_dir(superagents_dir) / "history"


def sa_tasks_dir(superagents_dir: Path) -> Path:
    return superagents_dir / "tasks"


def sa_task_dir(superagents_dir: Path, name: str) -> Path:
    return sa_tasks_dir(superagents_dir) / name


def sa_task_change_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_dir(superagents_dir, name) / "change"


def sa_task_plan_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_dir(superagents_dir, name) / "plan"


def sa_task_runs_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_dir(superagents_dir, name) / "runs"


def sa_change_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_change_dir(superagents_dir, name)


def sa_plan_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_plan_dir(superagents_dir, name)


def sa_runs_dir(superagents_dir: Path, name: str) -> Path:
    return sa_task_runs_dir(superagents_dir, name)


def sa_change_md(superagents_dir: Path, name: str) -> Path:
    d = sa_change_dir(superagents_dir, name)
    return d / "change.md"


def sa_task_md(superagents_dir: Path, name: str) -> Path:
    d = sa_plan_dir(superagents_dir, name)
    return d / "task.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def render_template(template_text: str, values: Mapping[str, str]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group("key")
        if key not in values:
            raise KeyError(f"模板缺少变量: {key}")
        return str(values[key])

    return PLACEHOLDER_RE.sub(repl, template_text)


def extract_frontmatter_value(markdown: str, key: str) -> Optional[str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_lines = lines[1:i]
            break
    else:
        return None

    prefix = f"{key}:"
    for line in fm_lines:
        if not line.startswith(prefix):
            continue
        return line[len(prefix) :].strip().strip('"').strip("'")
    return None
