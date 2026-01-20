#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import sa_id
from sa_util import extract_frontmatter_value


NAME_RE = re.compile(r"^(?P<padded_id>\d{6})_(?P<type>[a-z]+)_(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
SPEC_REF_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*$")

CHANGE_STATUS = {"draft", "review", "approved", "in_progress", "done", "rejected", "canceled"}
PLAN_STATUS = {"planned", "in_progress", "done", "blocked", "canceled"}
SPEC_STATUS = {"draft", "active", "deprecated"}
RUN_STATUS = {"success", "partial", "failure"}
RISK_LEVEL = {"low", "medium", "high", "critical"}

REQUIRED_SPEC_H2 = (
    "目标",
    "范围",
    "非目标",
    "背景与动机",
    "关键概念/术语",
    "用户故事 / 场景",
    "需求与规则（FR）",
    "非功能性需求（NFR）",
    "验收标准（AC）",
    "错误处理与边界条件",
    "开放问题",
)
REQUIRED_CHANGE_H2 = (
    "背景/动机",
    "范围（In/Out）",
    "头脑风暴（备选方案）",
    "评分与门禁（Clarity Score）",
    "变更内容",
    "影响分析",
    "验收标准变更",
    "回滚方案",
    "开放问题",
)
REQUIRED_PLAN_H2 = (
    "目标与成功标准",
    "就绪检查与评分（Readiness Score）",
    "任务清单",
    "实施步骤",
    "验证计划",
    "回滚计划",
    "风险与缓解",
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_validate.py", description="校验 superagents 目录结构与命名/元数据一致性")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    return p.parse_args(argv)


def err(msg: str) -> None:
    print(f"[sa_validate] 错误: {msg}", file=os.sys.stderr)


def parse_int(value: str, *, min_value: int, max_value: int, path: Path, field: str) -> tuple[bool, int]:
    try:
        parsed = int(str(value).strip())
    except ValueError:
        return False, 0
    if parsed < min_value or parsed > max_value:
        return False, parsed
    return True, parsed


def validate_required_h2(markdown: str, required: tuple[str, ...], path: Path, doc_label: str) -> list[str]:
    problems: list[str] = []
    for h in required:
        needle = f"## {h}"
        if needle not in markdown:
            problems.append(f"{doc_label} 缺少二级标题（需严格保留模板标题）：{needle}: {path}")
    return problems


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


def parse_csv_list(value: str) -> list[str]:
    items = []
    for part in re.split(r"[,\n]", str(value or "")):
        p = part.strip()
        if not p:
            continue
        items.append(p)
    return items


def is_substantive_text(text: str, *, allow_na: bool = False) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    if allow_na and re.search(r"\b(N/?A|不适用)\b", stripped, flags=re.IGNORECASE):
        return True
    compact = re.sub(r"[`>*#\-\[\]\(\)_\s]", "", stripped)
    if not compact:
        return False
    if re.fullmatch(r"[.。…，,;；:：]+", compact or ""):
        return False
    if re.search(r"\b(TODO|TBD|WIP)\b", stripped, flags=re.IGNORECASE):
        return False
    return bool(re.search(r"[A-Za-z0-9\u4e00-\u9fff]", stripped))


def validate_run_record(run_md: Path, expected_stable_id: str, expected_name: str) -> list[str]:
    problems: list[str] = []
    text = run_md.read_text(encoding="utf-8")
    doc_id = extract_frontmatter_value(text, "id")
    doc_schema = extract_frontmatter_value(text, "schema_version")
    doc_title = extract_frontmatter_value(text, "title")
    doc_status = extract_frontmatter_value(text, "status")
    doc_revision = extract_frontmatter_value(text, "revision") or ""
    doc_code_refs = extract_frontmatter_value(text, "code_refs") or ""
    doc_spec_refs = extract_frontmatter_value(text, "spec_refs") or ""
    doc_risk_level = extract_frontmatter_value(text, "risk_level")
    doc_change_name = extract_frontmatter_value(text, "change_name") or ""
    doc_plan_name = extract_frontmatter_value(text, "plan_name") or ""
    doc_started_at = extract_frontmatter_value(text, "started_at")
    doc_created_at = extract_frontmatter_value(text, "created_at")
    doc_updated_at = extract_frontmatter_value(text, "updated_at")

    if not doc_id:
        problems.append(f"run 缺少 frontmatter id: {run_md}")
    if not doc_schema:
        problems.append(f"run 缺少 frontmatter schema_version: {run_md}")
    if not doc_title:
        problems.append(f"run 缺少 frontmatter title: {run_md}")
    if not doc_status:
        problems.append(f"run 缺少 frontmatter status: {run_md}")
    if not doc_started_at:
        problems.append(f"run 缺少 frontmatter started_at: {run_md}")
    if not doc_created_at:
        problems.append(f"run 缺少 frontmatter created_at: {run_md}")
    if not doc_updated_at:
        problems.append(f"run 缺少 frontmatter updated_at: {run_md}")

    if doc_id and doc_id != expected_stable_id:
        problems.append(f"run id 不匹配（{doc_id} != {expected_stable_id}）: {run_md}")
    if doc_status and doc_status not in RUN_STATUS:
        problems.append(f"run status 不在枚举中（{sorted(RUN_STATUS)}）: {run_md}")

    if doc_schema:
        ok, parsed = parse_int(doc_schema, min_value=1, max_value=999, path=run_md, field="schema_version")
        if not ok:
            problems.append(f"run schema_version 非法（需为 1-999 整数）：{run_md}")
        elif parsed >= 2:
            if doc_risk_level is None:
                problems.append(f"run 缺少 frontmatter risk_level: {run_md}")
            elif doc_risk_level not in RISK_LEVEL:
                problems.append(f"run risk_level 不在枚举中（{sorted(RISK_LEVEL)}）: {run_md}")
            if not doc_change_name:
                problems.append(f"run 缺少 frontmatter change_name: {run_md}")
            elif doc_change_name != expected_name:
                problems.append(f"run change_name 不匹配（{doc_change_name} != {expected_name}）: {run_md}")
            if not doc_plan_name:
                problems.append(f"run 缺少 frontmatter plan_name: {run_md}")
            elif doc_plan_name != expected_name:
                problems.append(f"run plan_name 不匹配（{doc_plan_name} != {expected_name}）: {run_md}")

            if doc_status in {"success", "partial", "failure"}:
                if not parse_csv_list(doc_spec_refs):
                    problems.append(f"run.status={doc_status} 但 spec_refs 为空（追溯链缺失）: {run_md}")
                else:
                    superagents_dir = run_md.parent.parent.parent
                    for ref in parse_csv_list(doc_spec_refs):
                        if not SPEC_REF_RE.match(ref):
                            problems.append(f"run spec_refs 条目格式不合法（需 domain/capability）：{ref}: {run_md}")
                            continue
                        domain, capability = ref.split("/", 1)
                        spec_md = superagents_dir / "specs" / domain / capability / "spec.md"
                        if not spec_md.exists():
                            problems.append(f"run spec_refs 引用的 spec 不存在：{ref}: {run_md}")

            if doc_status == "success" and (not doc_revision and not parse_csv_list(doc_code_refs)):
                problems.append(f"run.status=success 但 revision/code_refs 均为空（无法定位代码版本）: {run_md}")

            if doc_status == "success" and (doc_risk_level or "") in {"high", "critical"}:
                evidence = section_body(text, "证据（日志/截图/命令输出）")
                if not is_substantive_text(evidence):
                    problems.append(f"risk_level={doc_risk_level} 且 run=success，但证据段为空: {run_md}")

    return problems


def validate_change(task_dir: Path) -> list[str]:
    problems: list[str] = []
    m = NAME_RE.match(task_dir.name)
    if not m:
        problems.append(f"tasks 目录命名不合法: {task_dir.name}")
        return problems
    if m.group("type") not in sa_id.TYPE_CHOICES:
        problems.append(f"tasks 目录 type 不在枚举中: {task_dir.name}")

    change_md = task_dir / "change" / "change.md"
    if not change_md.exists():
        problems.append(f"缺少 change.md: {change_md}")
        return problems

    text = change_md.read_text(encoding="utf-8")
    doc_id = extract_frontmatter_value(text, "id")
    doc_schema = extract_frontmatter_value(text, "schema_version")
    doc_title = extract_frontmatter_value(text, "title")
    doc_status = extract_frontmatter_value(text, "status")
    doc_type = extract_frontmatter_value(text, "type")
    doc_slug = extract_frontmatter_value(text, "slug")
    doc_clarity_score = extract_frontmatter_value(text, "clarity_score")
    doc_spec_refs = extract_frontmatter_value(text, "spec_refs")
    doc_risk_level = extract_frontmatter_value(text, "risk_level")

    padded_id = m.group("padded_id")
    expected_doc_ids = {f"CHG-{padded_id}"}
    if not doc_id:
        problems.append(f"change.md 缺少 frontmatter id: {change_md}")
    if not doc_schema:
        problems.append(f"change.md 缺少 frontmatter schema_version: {change_md}")
    if not doc_title:
        problems.append(f"change.md 缺少 frontmatter title: {change_md}")
    if not doc_status:
        problems.append(f"change.md 缺少 frontmatter status: {change_md}")
    if not doc_type:
        problems.append(f"change.md 缺少 frontmatter type: {change_md}")
    if not doc_slug:
        problems.append(f"change.md 缺少 frontmatter slug: {change_md}")
    if not doc_clarity_score:
        problems.append(f"change.md 缺少 frontmatter clarity_score: {change_md}")
    if doc_status and doc_status not in CHANGE_STATUS:
        problems.append(f"change.md status 不在枚举中（{sorted(CHANGE_STATUS)}）: {change_md}")
    if doc_id and doc_id not in expected_doc_ids:
        problems.append(f"change.md id 不匹配（{doc_id}；应为 CHG-{padded_id}）: {change_md}")
    if doc_type and doc_type != m.group("type"):
        problems.append(f"change.md type 不匹配（{doc_type} != {m.group('type')}）: {change_md}")
    if doc_slug and doc_slug != m.group("slug"):
        problems.append(f"change.md slug 不匹配（{doc_slug} != {m.group('slug')}）: {change_md}")

    problems.extend(validate_required_h2(text, REQUIRED_CHANGE_H2, change_md, "change.md"))

    if doc_schema:
        ok, parsed = parse_int(doc_schema, min_value=1, max_value=999, path=change_md, field="schema_version")
        if not ok:
            problems.append(f"change.md schema_version 非法（需为 1-999 整数）：{change_md}")
        elif parsed >= 2:
            if doc_spec_refs is None:
                problems.append(f"change.md 缺少 frontmatter spec_refs: {change_md}")
            if doc_risk_level is None:
                problems.append(f"change.md 缺少 frontmatter risk_level: {change_md}")
            elif doc_risk_level not in RISK_LEVEL:
                problems.append(f"change.md risk_level 不在枚举中（{sorted(RISK_LEVEL)}）: {change_md}")
            if (doc_status or "") in {"approved", "in_progress", "done"}:
                refs = parse_csv_list(doc_spec_refs or "")
                if not refs:
                    problems.append(f"change.status={doc_status} 但 spec_refs 为空（追溯链缺失）: {change_md}")
                else:
                    superagents_dir = task_dir.parent.parent
                    for ref in refs:
                        if not SPEC_REF_RE.match(ref):
                            problems.append(f"change spec_refs 条目格式不合法（需 domain/capability）：{ref}: {change_md}")
                            continue
                        domain, capability = ref.split("/", 1)
                        spec_md = superagents_dir / "specs" / domain / capability / "spec.md"
                        if not spec_md.exists():
                            problems.append(f"change spec_refs 引用的 spec 不存在：{ref}: {change_md}")

                for h2 in (
                    "背景/动机",
                    "范围（In/Out）",
                    "头脑风暴（备选方案）",
                    "影响分析",
                    "验收标准变更",
                    "风险与缓解",
                    "回滚方案",
                ):
                    body = section_body(text, h2)
                    if not is_substantive_text(body):
                        problems.append(f"change.status={doc_status} 但 {h2} 内容为空: {change_md}")

                brainstorm = section_body(text, "头脑风暴（备选方案）")
                if is_substantive_text(brainstorm):
                    if not re.search(r"(不需要|无需|单方案)", brainstorm):
                        count = len(re.findall(r"###\s*方案|方案\s*[A-Z]", brainstorm))
                        if count < 2:
                            problems.append(f"change.status={doc_status} 但头脑风暴备选方案不足（建议≥2）：{change_md}")

                if (doc_risk_level or "") in {"high", "critical"}:
                    for h2 in ("发布/灰度计划（如适用）", "兼容性/迁移"):
                        body = section_body(text, h2)
                        if not is_substantive_text(body, allow_na=True):
                            problems.append(f"risk_level={doc_risk_level} 但 {h2} 未明确（可写 不适用/N-A 说明原因）: {change_md}")

    if doc_clarity_score:
        ok, parsed = parse_int(doc_clarity_score, min_value=0, max_value=10, path=change_md, field="clarity_score")
        if not ok:
            problems.append(f"change.md clarity_score 非法（需为 0-10 整数）：{change_md}")
        elif (doc_status or "") in {"approved", "in_progress", "done"} and parsed < 7:
            problems.append(f"change.status={doc_status} 但 clarity_score<{7}（门禁未通过）: {change_md}")

    return problems


def validate_spec(spec_path: Path) -> list[str]:
    problems: list[str] = []
    text = spec_path.read_text(encoding="utf-8")
    doc_id = extract_frontmatter_value(text, "id")
    doc_schema = extract_frontmatter_value(text, "schema_version")
    doc_title = extract_frontmatter_value(text, "title")
    doc_status = extract_frontmatter_value(text, "status")
    doc_domain = extract_frontmatter_value(text, "domain")
    doc_capability = extract_frontmatter_value(text, "capability")
    if not doc_id:
        problems.append(f"spec.md 缺少 frontmatter id: {spec_path}")
    if not doc_schema:
        problems.append(f"spec.md 缺少 frontmatter schema_version: {spec_path}")
    if not doc_title:
        problems.append(f"spec.md 缺少 frontmatter title: {spec_path}")
    if not doc_status:
        problems.append(f"spec.md 缺少 frontmatter status: {spec_path}")
    if not doc_domain:
        problems.append(f"spec.md 缺少 frontmatter domain: {spec_path}")
    if not doc_capability:
        problems.append(f"spec.md 缺少 frontmatter capability: {spec_path}")
    if doc_status and doc_status not in SPEC_STATUS:
        problems.append(f"spec.md status 不在枚举中（{sorted(SPEC_STATUS)}）: {spec_path}")
    expected_domain = spec_path.parent.parent.name
    expected_capability = spec_path.parent.name
    if doc_domain and doc_domain != expected_domain:
        problems.append(f"spec.md domain 不匹配（{doc_domain} != {expected_domain}）: {spec_path}")
    if doc_capability and doc_capability != expected_capability:
        problems.append(f"spec.md capability 不匹配（{doc_capability} != {expected_capability}）: {spec_path}")

    problems.extend(validate_required_h2(text, REQUIRED_SPEC_H2, spec_path, "spec.md"))

    schema_version_num = 0
    if doc_schema:
        ok, parsed = parse_int(doc_schema, min_value=1, max_value=999, path=spec_path, field="schema_version")
        if not ok:
            problems.append(f"spec.md schema_version 非法（需为 1-999 整数）：{spec_path}")
        else:
            schema_version_num = parsed

    # active 门禁：AC 段至少包含一个条目（避免空规范上线）
    if (doc_status or "") == "active":
        ac_body = section_body(text, "验收标准（AC）")
        has_item = bool(re.search(r"^\s*-\s*(\[[ xX]\]\s*)?.+", ac_body, flags=re.MULTILINE))
        if not has_item:
            problems.append(f"spec.status=active 但 AC 为空: {spec_path}")

        if schema_version_num >= 2:
            ac_ids: list[str] = []
            for line in ac_body.splitlines():
                if not re.match(r"^\s*-\s*(\[[ xX]\]\s*)?.+", line):
                    continue
                m = re.search(r"\bAC-(\d{3})\b", line)
                if not m:
                    problems.append(f"spec.schema_version>=2 且 active，但存在未编号 AC 条目（需 AC-001 格式）: {spec_path}")
                    break
                ac_ids.append(f"AC-{m.group(1)}")
            if ac_ids and len(set(ac_ids)) != len(ac_ids):
                problems.append(f"spec.schema_version>=2 且 active，但 AC 编号重复: {spec_path}")

    if schema_version_num >= 2:
        fr_body = section_body(text, "需求与规则（FR）")
        for h3 in ("### MUST", "### SHOULD", "### MAY"):
            if h3 not in fr_body:
                problems.append(f"spec.schema_version>=2 缺少 FR 小节标题（需保留模板标题）：{h3}: {spec_path}")

        nfr_body = section_body(text, "非功能性需求（NFR）")
        for h3 in (
            "### 性能",
            "### 安全",
            "### 可靠性",
            "### 可观测性（日志/指标/告警）",
            "### 可维护性",
        ):
            if h3 not in nfr_body:
                problems.append(f"spec.schema_version>=2 缺少 NFR 小节标题（需保留模板标题）：{h3}: {spec_path}")

    if schema_version_num >= 3 and (doc_status or "") == "active":
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

        fr_body = section_body(text, "需求与规则（FR）")
        fr_ids: list[str] = []
        fr_has_any = False
        for block_title in ("MUST", "SHOULD", "MAY"):
            b = h3_block(fr_body, block_title)
            for line in b.splitlines():
                if not re.match(r"^\s*-\s*(\[[ xX]\]\s*)?.+", line):
                    continue
                fr_has_any = True
                m = re.search(r"\bFR-(\d{3})\b", line)
                if not m:
                    problems.append(f"spec.schema_version>=3 且 active，但存在未编号 FR 条目（需 FR-001 格式）: {spec_path}")
                    break
                fr_ids.append(f"FR-{m.group(1)}")
        if not fr_has_any:
            problems.append(f"spec.schema_version>=3 且 active，但 FR 为空: {spec_path}")
        if fr_ids and len(set(fr_ids)) != len(fr_ids):
            problems.append(f"spec.schema_version>=3 且 active，但 FR 编号重复: {spec_path}")

        nfr_body = section_body(text, "非功能性需求（NFR）")
        nfr_ids: list[str] = []
        nfr_has_any = False
        for block_title in ("性能", "安全", "可靠性", "可观测性（日志/指标/告警）", "可维护性"):
            b = h3_block(nfr_body, block_title)
            for line in b.splitlines():
                if not re.match(r"^\s*-\s*(\[[ xX]\]\s*)?.+", line):
                    continue
                nfr_has_any = True
                m = re.search(r"\bNFR-(\d{3})\b", line)
                if not m:
                    problems.append(f"spec.schema_version>=3 且 active，但存在未编号 NFR 条目（需 NFR-001 格式）: {spec_path}")
                    break
                nfr_ids.append(f"NFR-{m.group(1)}")
        if not nfr_has_any:
            problems.append(f"spec.schema_version>=3 且 active，但 NFR 为空: {spec_path}")
        if nfr_ids and len(set(nfr_ids)) != len(nfr_ids):
            problems.append(f"spec.schema_version>=3 且 active，但 NFR 编号重复: {spec_path}")
    return problems


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir

    required_dirs = ("specs", "tasks", ".sa", ".sa/wiki", ".sa/templates", ".sa/history")
    problems: list[str] = []
    for d in required_dirs:
        if not (superagents_dir / d).exists():
            problems.append(f"缺少目录: {os.path.relpath(str(superagents_dir / d), str(root))}")

    tasks_dir = superagents_dir / "tasks"
    if tasks_dir.exists():
        for task_dir in tasks_dir.iterdir():
            if not task_dir.is_dir():
                continue

            problems.extend(validate_change(task_dir))

            plan_dir = task_dir / "plan"
            task_md = plan_dir / "task.md"
            if not plan_dir.exists():
                problems.append(f"缺少 plan 目录: {plan_dir}")
                continue
            if not task_md.exists():
                problems.append(f"缺少 task.md: {task_md}")
                continue

            change_md = task_dir / "change" / "change.md"
            change_text = change_md.read_text(encoding="utf-8") if change_md.exists() else ""
            change_status = extract_frontmatter_value(change_text, "status") or ""
            change_schema_num = 0
            change_schema = extract_frontmatter_value(change_text, "schema_version")
            if change_schema:
                ok, parsed = parse_int(change_schema, min_value=1, max_value=999, path=change_md, field="schema_version")
                if ok:
                    change_schema_num = parsed
            change_id = extract_frontmatter_value(change_text, "id") or ""
            change_spec_refs = extract_frontmatter_value(change_text, "spec_refs") or ""
            change_risk_level = extract_frontmatter_value(change_text, "risk_level") or ""

            text = task_md.read_text(encoding="utf-8")
            plan_id = extract_frontmatter_value(text, "id")
            plan_schema = extract_frontmatter_value(text, "schema_version")
            plan_title = extract_frontmatter_value(text, "title")
            plan_status = extract_frontmatter_value(text, "status") or ""
            plan_readiness_score = extract_frontmatter_value(text, "readiness_score")
            plan_spec_refs = extract_frontmatter_value(text, "spec_refs")
            plan_risk_level = extract_frontmatter_value(text, "risk_level")

            padded_id = task_dir.name.split("_", 1)[0]
            expected_plan_id = f"CHG-{padded_id}"
            if not plan_id:
                problems.append(f"task.md 缺少 frontmatter id: {task_md}")
            elif change_id and plan_id != change_id:
                problems.append(f"task.md id 必须与 change.md id 一致（{plan_id} != {change_id}）: {task_md}")
            elif plan_id != expected_plan_id:
                problems.append(f"task.md id 不匹配（{plan_id}；应为 {expected_plan_id}）: {task_md}")
            if not plan_schema:
                problems.append(f"task.md 缺少 frontmatter schema_version: {task_md}")
            if not plan_title:
                problems.append(f"task.md 缺少 frontmatter title: {task_md}")
            if not plan_status:
                problems.append(f"task.md 缺少 frontmatter status: {task_md}")
            if plan_status and plan_status not in PLAN_STATUS:
                problems.append(f"task.md status 不在枚举中（{sorted(PLAN_STATUS)}）: {task_md}")
            if not plan_readiness_score:
                problems.append(f"task.md 缺少 frontmatter readiness_score: {task_md}")

            problems.extend(validate_required_h2(text, REQUIRED_PLAN_H2, task_md, "task.md"))

            plan_schema_num = 0
            if plan_schema:
                ok, parsed = parse_int(plan_schema, min_value=1, max_value=999, path=task_md, field="schema_version")
                if not ok:
                    problems.append(f"task.md schema_version 非法（需为 1-999 整数）：{task_md}")
                else:
                    plan_schema_num = parsed

            if plan_schema_num >= 2:
                if plan_spec_refs is None:
                    problems.append(f"task.md 缺少 frontmatter spec_refs: {task_md}")
                if plan_risk_level is None:
                    problems.append(f"task.md 缺少 frontmatter risk_level: {task_md}")
                elif plan_risk_level not in RISK_LEVEL:
                    problems.append(f"task.md risk_level 不在枚举中（{sorted(RISK_LEVEL)}）: {task_md}")
                refs = parse_csv_list(plan_spec_refs or "")
                if plan_status in {"in_progress", "done"} and not refs:
                    problems.append(f"plan.status={plan_status} 但 spec_refs 为空（追溯链缺失）: {task_md}")
                for ref in refs:
                    if not SPEC_REF_RE.match(ref):
                        problems.append(f"plan spec_refs 条目格式不合法（需 domain/capability）：{ref}: {task_md}")
                        continue
                    domain, capability = ref.split("/", 1)
                    spec_md = superagents_dir / "specs" / domain / capability / "spec.md"
                    if not spec_md.exists():
                        problems.append(f"plan spec_refs 引用的 spec 不存在：{ref}: {task_md}")

                if change_schema_num >= 2 and change_spec_refs and refs and set(parse_csv_list(change_spec_refs)) != set(refs):
                    problems.append(f"plan spec_refs 与 change spec_refs 不一致: {task_md}")

                if change_schema_num >= 2 and change_risk_level and plan_risk_level and change_risk_level != plan_risk_level:
                    problems.append(f"plan risk_level 与 change risk_level 不一致: {task_md}")

                if plan_status in {"in_progress", "done"}:
                    for h2 in ("实施步骤", "验证计划", "回滚计划", "风险与缓解"):
                        body = section_body(text, h2)
                        if not is_substantive_text(body):
                            problems.append(f"plan.status={plan_status} 但 {h2} 内容为空: {task_md}")

            if plan_readiness_score:
                ok, parsed = parse_int(
                    plan_readiness_score,
                    min_value=0,
                    max_value=10,
                    path=task_md,
                    field="readiness_score",
                )
                if not ok:
                    problems.append(f"task.md readiness_score 非法（需为 0-10 整数）：{task_md}")
                elif plan_status in {"in_progress", "done"} and parsed < 7:
                    problems.append(f"plan.status={plan_status} 但 readiness_score<{7}（门禁未通过）: {task_md}")

            if plan_status == "done":
                runs_dir = task_dir / "runs"
                run_records = []
                if runs_dir.exists():
                    run_records = [p for p in runs_dir.glob("*.md") if p.is_file()]
                if not run_records:
                    problems.append(f"plan=done 但缺少 runs 记录: {runs_dir}")
                else:
                    expected_stable_id = plan_id or f"CHG-{padded_id}"
                    has_success = False
                    for run_md in sorted(run_records):
                        problems.extend(
                            validate_run_record(
                                run_md,
                                expected_stable_id=expected_stable_id,
                                expected_name=task_dir.name,
                            )
                        )
                        status = extract_frontmatter_value(run_md.read_text(encoding="utf-8"), "status") or ""
                        if status == "success":
                            has_success = True
                    if not has_success:
                        problems.append(f"plan=done 但不存在 success run: {runs_dir}")

            if change_status == "done" and plan_status != "done":
                problems.append(f"change=done 但 plan!=done: {change_md} -> {task_md}")
            if plan_status == "done" and change_status != "done":
                problems.append(f"plan=done 但 change!=done: {task_md} -> {change_md}")

    specs_dir = superagents_dir / "specs"
    if specs_dir.exists():
        for spec_path in specs_dir.glob("*/*/spec.md"):
            problems.extend(validate_spec(spec_path))

    if problems:
        for p in problems:
            err(p)
        return 2

    print("校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
