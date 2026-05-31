#!/usr/bin/env python3
"""
Audit the evidence trail required before delivering a lab report.

The script is intentionally stricter than a normal LaTeX validator. It checks
whether the agent left concrete artifacts for the workflow steps that are easy
to claim but easy to skip: requirement extraction, data review, visual checks,
unresolved questions, and independent teacher review.

Typical usage:
    python3 audit_workflow_evidence.py --init report.tex
    python3 audit_workflow_evidence.py report.tex --evidence results/workflow_evidence.json
    python3 audit_workflow_evidence.py report.tex --json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DONE_STATUSES = {"done", "complete", "completed", "passed", "verified", "ok", "已完成", "通过"}
NA_STATUSES = {"na", "n/a", "not_applicable", "not applicable", "不适用"}

REQUIRED_STAGES = [
    ("stage1_requirements", "阶段1 需求清单", True, False),
    ("stage2_data_review", "阶段2 数据审阅", True, False),
    ("stage3_processing", "阶段3 数据处理", True, False),
    ("stage4_visual_checks", "阶段4 逐图渲染检查", True, False),
    ("stage5_assets", "阶段5 外部素材与来源", False, True),
    ("stage6_report", "阶段6 报告源码", True, False),
    ("stage7_self_review", "阶段7 自检记录", True, False),
    ("stage7_teacher_review", "阶段7.5 独立教师评审", True, False),
    ("stage8_delivery", "阶段8 最终交付", True, False),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_path(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def relative_to_root(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(read_text(path))
    except FileNotFoundError:
        raise ValueError(f"evidence manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in evidence manifest: {exc}")


def find_graphics(tex_path: Path) -> list[dict[str, Any]]:
    if not tex_path.exists():
        return []
    text = read_text(tex_path)
    pattern = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    results = []
    for match in pattern.finditer(text):
        raw = match.group(1).strip()
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = tex_path.parent / candidate

        resolved = None
        for ext in ("", ".pdf", ".png", ".jpg", ".jpeg", ".eps"):
            test_path = Path(str(candidate) + ext)
            if test_path.exists():
                resolved = test_path.resolve()
                break

        results.append(
            {
                "line": text[: match.start()].count("\n") + 1,
                "raw": raw,
                "resolved": resolved,
            }
        )
    return results


def extract_params_input(tex_path: Path, root: Path) -> Path | None:
    if not tex_path.exists():
        return None
    text = read_text(tex_path)
    for match in re.finditer(r"\\input\{([^}]*params\.tex[^}]*)\}", text):
        return resolve_path(root, match.group(1))
    return None


def first_existing_path(root: Path, item: dict[str, Any]) -> Path | None:
    candidates: list[str] = []
    for key in ("path", "file", "artifact"):
        value = item.get(key)
        if isinstance(value, str):
            candidates.append(value)
    paths = item.get("paths")
    if isinstance(paths, list):
        candidates.extend(str(p) for p in paths if p)

    for value in candidates:
        path = resolve_path(root, value)
        if path and path.exists():
            return path
    return None


def has_declared_path(item: dict[str, Any]) -> bool:
    return bool(item.get("path") or item.get("file") or item.get("artifact") or item.get("paths"))


def status_kind(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in DONE_STATUSES:
        return "done"
    if text in NA_STATUSES:
        return "na"
    return "other"


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def issue_count(item: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = item.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return 0


def build_template(root: Path, report_path: Path | None, evidence_path: Path) -> dict[str, Any]:
    report_rel = relative_to_root(root, report_path) if report_path else "report.tex"
    report_pdf = str(Path(report_rel).with_suffix(".pdf"))
    graphics = find_graphics(report_path) if report_path else []

    figure_checks = []
    for item in graphics:
        raw = item["raw"]
        resolved = item["resolved"]
        figure_path = relative_to_root(root, resolved) if resolved else raw
        figure = Path(figure_path)
        preview = f"checks/{figure.stem}_p0_200dpi.png" if figure.suffix.lower() == ".pdf" else ""
        figure_checks.append(
            {
                "figure": figure_path,
                "preview_png": preview,
                "checked": False,
                "notes": "填写直接查看后的结论：无乱码、无重叠、无截断。",
            }
        )

    return {
        "schema_version": 1,
        "report_tex": report_rel,
        "report_pdf": report_pdf,
        "params_tex": "results/params.tex",
        "stage_evidence": {
            "stage1_requirements": {
                "status": "todo",
                "path": "results/requirements_checklist.md",
                "notes": "从讲义提取的硬性/建议/未明确要求清单。",
            },
            "stage2_data_review": {
                "status": "todo",
                "path": "results/data_review.md",
                "notes": "数据文件、单位、异常值、手写数据复核记录。",
            },
            "stage3_processing": {
                "status": "todo",
                "path": "results/processing_summary.md",
                "notes": "处理方法、脚本、关键结果和 params.tex 生成说明。",
            },
            "stage4_visual_checks": {
                "status": "todo",
                "path": "results/figure_review.md",
                "notes": "逐图直接查看记录。",
            },
            "stage5_assets": {
                "status": "not_applicable",
                "path": "",
                "notes": "无外部素材时保持 not_applicable；有外部图时改为 done 并填写 external_assets。",
            },
            "stage6_report": {
                "status": "todo",
                "path": report_rel,
                "notes": "报告源码。",
            },
            "stage7_self_review": {
                "status": "todo",
                "path": "reviews/self_review.md",
                "notes": "七维排查、逐页逐图逐句检查记录。",
            },
            "stage7_teacher_review": {
                "status": "todo",
                "path": "reviews/teacher_review.md",
                "notes": "独立教师评审输出。",
            },
            "stage8_delivery": {
                "status": "todo",
                "path": report_pdf,
                "notes": "最终 PDF。",
            },
        },
        "manual_data_review": {
            "has_handwritten_data": False,
            "methods": [],
            "unresolved_items": [],
        },
        "figure_checks": figure_checks,
        "external_assets": [],
        "teacher_reviews": [
            {
                "path": "reviews/teacher_review.md",
                "open_severe_issues": 0,
                "checked": False,
            }
        ],
        "unresolved_questions": [],
    }


def audit_manifest(root: Path, manifest: dict[str, Any], report_arg: Path | None, allow_draft: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    report_path = report_arg or resolve_path(root, manifest.get("report_tex"))
    if not report_path:
        errors.append("未声明 report_tex，也未在命令行传入报告路径。")
    elif not report_path.exists():
        errors.append(f"报告源码不存在: {relative_to_root(root, report_path)}")

    if report_path and report_path.exists():
        root = report_path.parent.resolve()

    pdf_path = resolve_path(root, manifest.get("report_pdf")) if manifest.get("report_pdf") else None
    if not pdf_path and report_path:
        pdf_path = report_path.with_suffix(".pdf")
    if pdf_path and not pdf_path.exists():
        message = f"最终 PDF 不存在: {relative_to_root(root, pdf_path)}"
        if allow_draft:
            warnings.append(message)
        else:
            errors.append(message)

    stage_evidence = manifest.get("stage_evidence") or manifest.get("stages") or {}
    if not isinstance(stage_evidence, dict):
        errors.append("stage_evidence 必须是对象。")
        stage_evidence = {}

    for key, label, path_required, allow_na in REQUIRED_STAGES:
        item = stage_evidence.get(key)
        if not isinstance(item, dict):
            errors.append(f"{label} 缺少 stage_evidence.{key}。")
            continue
        kind = status_kind(item.get("status"))
        if kind == "na":
            if not allow_na:
                errors.append(f"{label} 不能标记为不适用。")
            elif not str(item.get("notes", "")).strip():
                errors.append(f"{label} 标记为不适用时必须说明原因。")
            continue
        if kind != "done":
            errors.append(f"{label} 状态不是 done/通过: {item.get('status')!r}")
            continue
        if path_required or has_declared_path(item):
            if not first_existing_path(root, item):
                errors.append(f"{label} 缺少可访问的证据文件。")

    unresolved = as_list(manifest.get("unresolved_questions"))
    if unresolved:
        errors.append(f"仍有未解决问题 {len(unresolved)} 项，必须先向用户确认。")

    params_path = resolve_path(root, manifest.get("params_tex")) if manifest.get("params_tex") else None
    params_input = extract_params_input(report_path, root) if report_path else None
    params_path = params_path or params_input or resolve_path(root, "results/params.tex")
    if not params_input:
        errors.append("报告源码未检测到 \\input{...params.tex}，数值管线未接入 LaTeX。")
    if not params_path or not params_path.exists():
        errors.append(f"params.tex 不存在: {relative_to_root(root, params_path) if params_path else '未声明'}")

    manual_review = manifest.get("manual_data_review") or {}
    if manual_review.get("has_handwritten_data"):
        methods = [m for m in as_list(manual_review.get("methods")) if str(m).strip()]
        unresolved_items = as_list(manual_review.get("unresolved_items"))
        if len(methods) < 2:
            errors.append("存在手写数据时，manual_data_review.methods 至少需要两种独立复核方法。")
        if unresolved_items:
            errors.append(f"手写数据仍有未解决存疑项 {len(unresolved_items)} 项。")

    graphics = find_graphics(report_path) if report_path else []
    missing_graphics = [g for g in graphics if not g["resolved"]]
    for item in missing_graphics:
        errors.append(f"图片引用不存在: 第 {item['line']} 行 {item['raw']}")

    figure_checks = manifest.get("figure_checks") or []
    if graphics and not figure_checks:
        errors.append("报告包含图片，但 workflow_evidence.json 中没有 figure_checks。")
    check_map: dict[Path, dict[str, Any]] = {}
    for entry in figure_checks:
        if not isinstance(entry, dict):
            continue
        figure_value = entry.get("figure") or entry.get("path") or entry.get("file")
        figure_path = resolve_path(root, figure_value)
        if figure_path:
            check_map[figure_path] = entry
            if not figure_path.exists():
                errors.append(f"figure_checks 引用的图片不存在: {relative_to_root(root, figure_path)}")

    for item in graphics:
        resolved = item["resolved"]
        if not resolved:
            continue
        entry = check_map.get(resolved)
        if not entry:
            errors.append(f"图片缺少逐图检查证据: {relative_to_root(root, resolved)}")
            continue
        if entry.get("checked") is not True:
            errors.append(f"图片未标记为已直接查看: {relative_to_root(root, resolved)}")
        preview_value = entry.get("preview_png") or entry.get("preview")
        preview_path = resolve_path(root, preview_value)
        if resolved.suffix.lower() == ".pdf" and not (preview_path and preview_path.exists()):
            errors.append(f"PDF 图片缺少 PNG 预览证据: {relative_to_root(root, resolved)}")
        elif preview_value and not (preview_path and preview_path.exists()):
            warnings.append(f"声明的图片预览不存在: {preview_value}")

    for asset in as_list(manifest.get("external_assets")):
        if not isinstance(asset, dict):
            continue
        asset_path = resolve_path(root, asset.get("file") or asset.get("path"))
        if asset_path and not asset_path.exists():
            errors.append(f"外部素材文件不存在: {relative_to_root(root, asset_path)}")
        if not str(asset.get("source", "")).strip():
            errors.append("外部素材缺少 source 来源说明。")
        if asset.get("checked") is not True:
            errors.append("外部素材未标记为已检查裁剪/版权/显示质量。")

    reviews = manifest.get("teacher_reviews")
    if reviews is None and manifest.get("teacher_review") is not None:
        reviews = manifest.get("teacher_review")
    reviews_list = as_list(reviews)
    if not reviews_list:
        errors.append("缺少 teacher_reviews，阶段7.5 独立教师评审不能跳过。")
    for review in reviews_list:
        if not isinstance(review, dict):
            errors.append("teacher_reviews 条目必须是对象。")
            continue
        review_path = resolve_path(root, review.get("path") or review.get("file"))
        if not review_path or not review_path.exists():
            errors.append("教师评审缺少可访问的 review 文件。")
        if review.get("checked") is not True:
            errors.append("教师评审未标记为 checked=true。")
        severe = issue_count(review, "open_severe_issues", "severe_open", "open_severe")
        if severe > 0:
            errors.append(f"教师评审仍有严重问题未关闭: {severe} 项。")
        medium = issue_count(review, "open_medium_issues", "medium_open", "open_medium")
        if medium > 0:
            warnings.append(f"教师评审仍有中等问题未关闭: {medium} 项。")

    data_scripts = as_list(manifest.get("data_scripts"))
    for script in data_scripts:
        script_path = resolve_path(root, str(script))
        if script_path and not script_path.exists():
            errors.append(f"数据处理脚本不存在: {relative_to_root(root, script_path)}")

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "report_tex": relative_to_root(root, report_path) if report_path else None,
            "report_pdf": relative_to_root(root, pdf_path) if pdf_path else None,
            "params_tex": relative_to_root(root, params_path) if params_path else None,
            "graphics": len(graphics),
            "teacher_reviews": len(reviews_list),
        },
    }


def print_report(report: dict[str, Any]) -> None:
    print("\n" + "=" * 56)
    print("实验报告 workflow evidence 门禁")
    print("=" * 56)
    print(f"结果: {'通过' if report['passed'] else '未通过'}")
    checks = report.get("checks", {})
    print(f"报告源码: {checks.get('report_tex')}")
    print(f"最终 PDF: {checks.get('report_pdf')}")
    print(f"params.tex: {checks.get('params_tex')}")
    print(f"图片数量: {checks.get('graphics')}")
    print(f"教师评审: {checks.get('teacher_reviews')}")

    if report["errors"]:
        print("\n阻塞问题:")
        for item in report["errors"]:
            print(f"- {item}")
    if report["warnings"]:
        print("\n警告:")
        for item in report["warnings"]:
            print(f"- {item}")
    print("=" * 56 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查实验报告八阶段 workflow evidence 交付门禁")
    parser.add_argument("report", nargs="?", help="LaTeX 报告源码路径，例如 report.tex")
    parser.add_argument(
        "--evidence",
        default="results/workflow_evidence.json",
        help="workflow evidence JSON 路径，默认 results/workflow_evidence.json",
    )
    parser.add_argument("--init", action="store_true", help="创建 workflow_evidence.json 模板")
    parser.add_argument("--force", action="store_true", help="--init 时允许覆盖已有文件")
    parser.add_argument("--allow-draft", action="store_true", help="草稿模式：最终 PDF 缺失降级为警告")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args()

    report_path = Path(args.report).expanduser().resolve() if args.report else None
    root = report_path.parent if report_path else Path.cwd()
    evidence_path = Path(args.evidence).expanduser()
    if not evidence_path.is_absolute():
        evidence_path = root / evidence_path
    evidence_path = evidence_path.resolve()

    if args.init:
        if evidence_path.exists() and not args.force:
            print(f"evidence manifest already exists: {evidence_path}", file=sys.stderr)
            return 1
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        template = build_template(root, report_path, evidence_path)
        evidence_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已创建: {evidence_path}")
        return 0

    try:
        manifest = load_manifest(evidence_path)
    except ValueError as exc:
        report = {"passed": False, "errors": [str(exc)], "warnings": [], "checks": {}}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report)
        return 1

    audit = audit_manifest(root, manifest, report_path, allow_draft=args.allow_draft)
    if args.json:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    else:
        print_report(audit)
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
