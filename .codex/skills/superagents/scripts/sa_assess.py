#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from sa_util import extract_frontmatter_value


RISK_LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
RISK_LEVELS = set(RISK_LEVEL_ORDER.keys())

CHANGE_SECTION_TITLES = {
    "背景/动机": "problem",
    "范围（In/Out）": "scope",
    "验收标准变更": "acceptance",
    "影响分析": "impact",
    "回滚方案": "rollback",
}

PLAN_SECTION_TITLES = {
    "任务清单": "tasks",
    "验证计划": "verification",
    "风险与缓解": "risk",
    "回滚计划": "rollback",
    "就绪检查与评分（Readiness Score）": "dependencies",
}

CHECKBOX_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+.+", flags=re.MULTILINE)
CODE_FENCE_RE = re.compile(r"^```", flags=re.MULTILINE)
AC_ID_RE = re.compile(r"\bAC-\d{3}\b")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sa_assess.py", description="对 change/plan 的清晰度与就绪度做缺口分析，并给出追问清单")
    p.add_argument("--root", default=".", help="项目根目录（默认：当前目录）")
    p.add_argument("--dir", default="superagents", help="superagents 目录名（默认：superagents）")
    p.add_argument("--name", help="对象名（如 000123_feat_example）；不传则扫描全部 tasks")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果")
    return p.parse_args(argv)


def rel(root: Path, p: Path) -> str:
    return os.path.relpath(str(p), str(root))


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


def is_substantive(text: str) -> bool:
    stripped = re.sub(r"[`>*#\-\[\]\(\)_\s]", "", text)
    if not stripped:
        return False
    if re.fullmatch(r"[.。…，,;；:：]+", stripped or ""):
        return False
    if re.search(r"\b(TODO|TBD|WIP)\b", text, flags=re.IGNORECASE):
        return False
    return bool(re.search(r"[A-Za-z0-9\u4e00-\u9fff]", text))


def detect_risk(text: str) -> tuple[str, list[str]]:
    flags: list[str] = []
    level = "low"

    def bump(new_level: str) -> None:
        nonlocal level
        if RISK_LEVEL_ORDER[new_level] > RISK_LEVEL_ORDER[level]:
            level = new_level

    t = text or ""
    if re.search(r"\b(prod|production|live)\b|生产", t, flags=re.IGNORECASE):
        flags.append("prod_ops")
        bump("critical")
    if re.search(r"\bDROP\b|\bTRUNCATE\b|rm\s+-rf", t, flags=re.IGNORECASE):
        flags.append("destructive")
        bump("critical")
    if re.search(r"(密钥|secret|token|证书|key)", t, flags=re.IGNORECASE):
        flags.append("security")
        bump("high")
    if re.search(r"(支付|payment|refund|金额|对账)", t, flags=re.IGNORECASE):
        flags.append("payment")
        bump("high")
    if re.search(r"(权限|auth|认证|鉴权|RBAC|role)", t, flags=re.IGNORECASE):
        flags.append("auth")
        bump("high")
    if re.search(r"(迁移|migration|数据库|schema|DDL|表结构)", t, flags=re.IGNORECASE):
        flags.append("data_migration")
        bump("high")
    if re.search(r"(外部依赖|第三方|回调|webhook|mq|kafka)", t, flags=re.IGNORECASE):
        flags.append("external_dependency")
        bump("medium")

    if level == "low" and re.search(r"(跨模块|跨服务|接口|API|配置|缓存)", t, flags=re.IGNORECASE):
        bump("medium")

    # 去重但保持顺序
    seen: set[str] = set()
    uniq_flags: list[str] = []
    for f in flags:
        if f in seen:
            continue
        seen.add(f)
        uniq_flags.append(f)
    return level, uniq_flags


def score_change(text: str) -> tuple[int, list[str], list[str], dict[str, int]]:
    points_by: dict[str, int] = {}
    gaps: list[str] = []
    questions: list[str] = []

    def add(item: str, pts: int, gap: str | None, qs: list[str]) -> None:
        points_by[item] = pts
        if gap:
            gaps.append(gap)
        for q in qs:
            questions.append(q)

    # 1) 问题陈述清晰
    body = section_body(text, "背景/动机")
    if not is_substantive(body):
        add("problem", 0, "背景/动机 为空或占位", ["当前要解决的问题是什么？为什么现在要改？"])
    elif len(body) >= 80:
        add("problem", 2, None, [])
    else:
        add("problem", 1, "背景/动机 偏短（建议补充上下文/现状/痛点）", ["现状是什么？痛点/失败案例/数据证据是什么？"])

    # 2) 范围边界清晰
    body = section_body(text, "范围（In/Out）")
    if not is_substantive(body):
        add("scope", 0, "范围（In/Out）未明确", ["本次变更包含哪些（In）？不包含哪些（Out）？"])
    else:
        has_in = bool(re.search(r"\bIn\b|包含|纳入|覆盖", body))
        has_out = bool(re.search(r"\bOut\b|不包含|不做|排除", body))
        pts = 2 if (has_in and has_out) else 1
        gap = None if pts == 2 else "范围边界信息不足（建议明确 In/Out）"
        qs = [] if pts == 2 else ["哪些内容明确不做（Out）？有哪些容易越界的边界条件？"]
        add("scope", pts, gap, qs)

    # 3) 验收标准清晰
    body = section_body(text, "验收标准变更")
    if not is_substantive(body):
        add("acceptance", 0, "验收标准变更 未写", ["验收标准是什么？如何验证通过/失败？对应哪些 AC？"])
    else:
        pts = 2 if AC_ID_RE.search(body) else 1
        gap = None if pts == 2 else "验收标准缺少可引用的 AC 编号（建议写 AC-001...）"
        qs = [] if pts == 2 else ["能否把验收写成可编号的 AC（例如 AC-001）？失败时表现是什么？"]
        add("acceptance", pts, gap, qs)

    # 4) 影响分析清晰
    body = section_body(text, "影响分析")
    if not is_substantive(body):
        add("impact", 0, "影响分析 未写", ["会影响哪些模块/数据/API/用户？有哪些兼容性与迁移影响？"])
    else:
        pts = 2 if re.search(r"(模块|数据|API|用户|权限|配置|性能|可观测)", body) else 1
        gap = None if pts == 2 else "影响分析缺少可追踪的影响面（模块/数据/API/用户）"
        qs = [] if pts == 2 else ["具体影响面有哪些？是否需要迁移/兼容策略？"]
        add("impact", pts, gap, qs)

    # 5) 回滚可执行
    body = section_body(text, "回滚方案")
    if not is_substantive(body):
        add("rollback", 0, "回滚方案 未写", ["失败时如何回滚？触发条件是什么？回滚步骤是什么？"])
    else:
        has_steps = bool(re.search(r"^\s*(\d+\.|-)\s+", body, flags=re.MULTILINE))
        pts = 2 if (has_steps and len(body) >= 40) else 1
        gap = None if pts == 2 else "回滚方案偏弱（建议写清触发条件+步骤）"
        qs = [] if pts == 2 else ["回滚的触发条件是什么？具体步骤（含命令/配置）是什么？如何验证回滚成功？"]
        add("rollback", pts, gap, qs)

    # 额外：头脑风暴（不计入 0-10 分，但会给出缺口与追问）
    brainstorm = section_body(text, "头脑风暴（备选方案）")
    if not is_substantive(brainstorm):
        gaps.append("头脑风暴（备选方案）为空或占位（建议≥2个方案，并写清取舍）")
        questions.append("有哪些备选方案（至少2个）？每个方案的取舍/风险是什么？为什么选当前方案？")
    else:
        if not re.search(r"(不需要|无需|单方案)", brainstorm):
            count = len(re.findall(r"###\s*方案|方案\s*[A-Z]", brainstorm))
            if count < 2:
                gaps.append("头脑风暴备选方案不足（建议≥2）")
                questions.append("能否补齐至少2个备选方案，并说明为什么不选？")
        if not re.search(r"(产品/价值|架构/实现|测试/验证|运维/发布|安全/合规)", brainstorm):
            gaps.append("头脑风暴缺少多视角（产品/架构/测试/运维/安全）信息")
            questions.append("能否从产品/架构/测试/运维/安全五个视角补齐每个方案的要点？")

    return sum(points_by.values()), gaps, questions, points_by


def score_plan(text: str) -> tuple[int, list[str], list[str], dict[str, int]]:
    points_by: dict[str, int] = {}
    gaps: list[str] = []
    questions: list[str] = []

    def add(item: str, pts: int, gap: str | None, qs: list[str]) -> None:
        points_by[item] = pts
        if gap:
            gaps.append(gap)
        for q in qs:
            questions.append(q)

    # 1) 任务拆解可执行
    body = section_body(text, "任务清单")
    count = len(CHECKBOX_RE.findall(body or ""))
    if count == 0:
        add("tasks", 0, "任务清单 为空或无可执行项", ["需要拆解哪些任务？按模块/步骤列出可勾选清单。"])
    elif count >= 6:
        add("tasks", 2, None, [])
    else:
        add("tasks", 1, "任务清单偏少（建议细化到可执行粒度）", ["哪些任务需要再拆细（例如测试/迁移/可观测性）？"])

    # 2) 验证计划明确
    body = section_body(text, "验证计划")
    if not is_substantive(body):
        add("verification", 0, "验证计划 未写", ["如何验证？单测/集成/回归/人工验收分别做什么？"])
    else:
        pts = 2 if (CODE_FENCE_RE.search(body) or re.search(r"(单测|集成|回归|e2e|验收|压测|curl|pytest|jest|npm test)", body, flags=re.IGNORECASE)) else 1
        gap = None if pts == 2 else "验证计划缺少可执行的验证方式（建议写命令/场景/验收步骤）"
        qs = [] if pts == 2 else ["能否补充至少一条可执行的测试/验证命令或具体验收步骤？"]
        add("verification", pts, gap, qs)

    # 3) 风险与缓解明确
    body = section_body(text, "风险与缓解")
    if not is_substantive(body):
        add("risk", 0, "风险与缓解 未写", ["主要风险是什么？如何缓解/监控？失败预案是什么？"])
    else:
        has_bullets = bool(re.search(r"^\s*-\s+.+", body, flags=re.MULTILINE))
        pts = 2 if (has_bullets and re.search(r"(缓解|监控|应对|回退|降级)", body)) else 1
        gap = None if pts == 2 else "风险与缓解偏弱（建议列出风险→缓解→监控/预案）"
        qs = [] if pts == 2 else ["能否按“风险→缓解→监控/预案”结构补充？"]
        add("risk", pts, gap, qs)

    # 4) 回滚计划明确
    body = section_body(text, "回滚计划")
    if not is_substantive(body):
        add("rollback", 0, "回滚计划 未写", ["回滚条件是什么？回滚步骤是什么？回滚后如何验证？"])
    else:
        has_steps = bool(re.search(r"^\s*(\d+\.|-)\s+", body, flags=re.MULTILINE))
        pts = 2 if (has_steps and re.search(r"(条件|触发|验证)", body)) else 1
        gap = None if pts == 2 else "回滚计划偏弱（建议写清条件+步骤+验证）"
        qs = [] if pts == 2 else ["回滚触发条件与验证步骤分别是什么？"]
        add("rollback", pts, gap, qs)

    # 5) 依赖已确认（暂基于“就绪检查”段落）
    body = section_body(text, "就绪检查与评分（Readiness Score）")
    if not is_substantive(body):
        add("dependencies", 0, "就绪检查与评分 未写", ["有哪些外部依赖/权限/资源/时间窗需要提前确认？"])
    else:
        pts = 2 if re.search(r"(依赖|权限|资源|时间窗|证书|账号|环境|审批)", body) else 1
        gap = None if pts == 2 else "依赖信息不足（建议明确外部依赖/权限/资源/时间窗）"
        qs = [] if pts == 2 else ["是否需要特定权限/时间窗/外部资源？谁负责提供？"]
        add("dependencies", pts, gap, qs)

    return sum(points_by.values()), gaps, questions, points_by


def assess_one(root: Path, superagents_dir: Path, name: str) -> dict[str, Any]:
    change_md = superagents_dir / "tasks" / name / "change" / "change.md"
    task_md = superagents_dir / "tasks" / name / "plan" / "task.md"

    result: dict[str, Any] = {"name": name, "paths": {}}
    if change_md.exists():
        text = change_md.read_text(encoding="utf-8")
        status = extract_frontmatter_value(text, "status") or "unknown"
        score = extract_frontmatter_value(text, "clarity_score") or ""
        spec_refs = extract_frontmatter_value(text, "spec_refs") or ""
        risk_level = extract_frontmatter_value(text, "risk_level") or ""
        risk_suggested, risk_flags_suggested = detect_risk(text)
        suggested, gaps, questions, detail = score_change(text)
        if not spec_refs:
            gaps.append("spec_refs 为空（建议补齐 domain/capability 以建立追溯链）")
            questions.append("本次变更对应哪些 spec（domain/capability）？填入 change.md 的 spec_refs。")
        if not risk_level:
            gaps.append("risk_level 为空（建议明确风险等级：low/medium/high/critical）")
            questions.append("本次变更风险等级是什么？填入 change.md 的 risk_level。")
        elif risk_level not in RISK_LEVELS:
            gaps.append(f"risk_level 非法（{risk_level}），应为 {sorted(RISK_LEVELS)}")
        else:
            if RISK_LEVEL_ORDER.get(risk_suggested, 0) > RISK_LEVEL_ORDER.get(risk_level, 0):
                gaps.append(f"检测到风险信号，建议风险等级 >= {risk_suggested}（当前 {risk_level}）")
                questions.append(f"是否需要将 risk_level 提升到 {risk_suggested}？风险点：{', '.join(risk_flags_suggested) or 'unknown'}")
        result["change"] = {
            "status": status,
            "clarity_score": score,
            "clarity_suggested": suggested,
            "spec_refs": spec_refs,
            "risk_level": risk_level,
            "risk_suggested": risk_suggested,
            "risk_flags_suggested": risk_flags_suggested,
            "gaps": gaps,
            "questions": questions,
            "detail": detail,
        }
        result["paths"]["change"] = rel(root, change_md)
    else:
        result["change"] = {"missing": True}
        result["paths"]["change"] = rel(root, change_md)

    if task_md.exists():
        text = task_md.read_text(encoding="utf-8")
        status = extract_frontmatter_value(text, "status") or "unknown"
        score = extract_frontmatter_value(text, "readiness_score") or ""
        spec_refs = extract_frontmatter_value(text, "spec_refs") or ""
        risk_level = extract_frontmatter_value(text, "risk_level") or ""
        suggested, gaps, questions, detail = score_plan(text)
        if not spec_refs:
            gaps.append("spec_refs 为空（建议补齐 domain/capability 以建立追溯链）")
            questions.append("本次执行方案对应哪些 spec（domain/capability）？填入 task.md 的 spec_refs。")
        if not risk_level:
            gaps.append("risk_level 为空（建议与 change 保持一致）")
            questions.append("task.md 的 risk_level 是否与 change.md 一致？")
        result["plan"] = {
            "status": status,
            "readiness_score": score,
            "readiness_suggested": suggested,
            "spec_refs": spec_refs,
            "risk_level": risk_level,
            "gaps": gaps,
            "questions": questions,
            "detail": detail,
        }
        result["paths"]["plan"] = rel(root, task_md)
    else:
        result["plan"] = {"missing": True}
        result["paths"]["plan"] = rel(root, task_md)

    return result


def render_human(result: dict[str, Any]) -> str:
    lines: list[str] = [f"[sa_assess] {result['name']}"]

    change = result.get("change", {})
    if change.get("missing"):
        lines.append(f"- change: 缺失 ({result['paths'].get('change')})")
    else:
        spec_refs = change.get("spec_refs") or ""
        spec_note = f", spec_refs={spec_refs}" if spec_refs else ", spec_refs=<empty>"
        risk_level = change.get("risk_level") or ""
        risk_suggested = change.get("risk_suggested") or ""
        risk_note = f", risk={risk_level}" if risk_level else ", risk=<empty>"
        if risk_suggested and risk_suggested != risk_level:
            risk_note += f" (suggested>={risk_suggested})"
        lines.append(
            f"- change: status={change.get('status')}, clarity={change.get('clarity_score')} -> suggested={change.get('clarity_suggested')}{spec_note}{risk_note}"
        )
        for g in change.get("gaps") or []:
            lines.append(f"  - gap: {g}")
        qs = change.get("questions") or []
        if qs:
            lines.append("  - questions:")
            for i, q in enumerate(qs, start=1):
                lines.append(f"    {i}. {q}")

    plan = result.get("plan", {})
    if plan.get("missing"):
        lines.append(f"- plan: 缺失 ({result['paths'].get('plan')})")
    else:
        spec_refs = plan.get("spec_refs") or ""
        spec_note = f", spec_refs={spec_refs}" if spec_refs else ", spec_refs=<empty>"
        risk_level = plan.get("risk_level") or ""
        risk_note = f", risk={risk_level}" if risk_level else ", risk=<empty>"
        lines.append(
            f"- plan: status={plan.get('status')}, ready={plan.get('readiness_score')} -> suggested={plan.get('readiness_suggested')}{spec_note}{risk_note}"
        )
        for g in plan.get("gaps") or []:
            lines.append(f"  - gap: {g}")
        qs = plan.get("questions") or []
        if qs:
            lines.append("  - questions:")
            for i, q in enumerate(qs, start=1):
                lines.append(f"    {i}. {q}")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    superagents_dir = root / args.dir
    if not superagents_dir.exists():
        raise FileNotFoundError(f"未找到 {superagents_dir}，请先运行 sa_init.py 初始化 superagents/")

    names: list[str] = []
    if args.name:
        names = [args.name.strip()]
    else:
        tasks_dir = superagents_dir / "tasks"
        if tasks_dir.exists():
            names = sorted([p.name for p in tasks_dir.iterdir() if p.is_dir()])

    results = [assess_one(root, superagents_dir, name) for name in names]

    if args.json:
        print(json.dumps({"root": str(root), "results": results}, ensure_ascii=False))
        return 0

    for r in results:
        print(render_human(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
