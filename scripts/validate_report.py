#!/usr/bin/env python3
"""
实验报告综合验证脚本

一键执行多项检查，在提交前快速发现常见问题：
1. 图片存在性检查（所有 \\includegraphics 引用的图片是否都存在）
2. 数值管线检查（扫描手动输入的数值）
3. LaTeX 编译测试（自动编译并报告错误/警告）
4. Workflow evidence 门禁（八阶段证据 + 逐图查看 + 教师评审）
5. 报告文件大小检查

用法:
    # 完整验证
    python3 validate_report.py report.tex

    # 仅检查图片
    python3 validate_report.py report.tex --check-images-only

    # 跳过编译（仅做静态检查）
    python3 validate_report.py report.tex --no-compile

    # 草稿/排错时跳过 workflow evidence 门禁
    python3 validate_report.py report.tex --skip-workflow-evidence

    # 输出 JSON 格式（用于 CI/自动化）
    python3 validate_report.py report.tex --json
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def find_graphics(tex_path: Path) -> list[dict]:
    r"""查找所有 \includegraphics 引用的图片"""
    text = tex_path.read_text(encoding="utf-8")
    # 匹配 \includegraphics[...]{path}
    pattern = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
    results = []
    for match in pattern.finditer(text):
        img_path = match.group(1)
        # 处理相对路径
        if not img_path.startswith('/'):
            candidate = tex_path.parent / img_path
        else:
            candidate = Path(img_path)
        
        # 尝试常见扩展名
        exists = False
        resolved = None
        for ext in ['', '.pdf', '.png', '.jpg', '.jpeg', '.eps']:
            test = Path(str(candidate) + ext)
            if test.exists():
                exists = True
                resolved = test
                break
        
        results.append({
            "line": text[:match.start()].count('\n') + 1,
            "path": img_path,
            "exists": exists,
            "resolved": str(resolved) if resolved else None,
        })
    return results


def check_params_tex(tex_path: Path) -> dict:
    """检查是否使用了数值管线（params.tex）"""
    text = tex_path.read_text(encoding="utf-8")
    has_input_params = bool(re.search(r'\\input\{[^}]*params\.tex[^}]*\}', text))
    
    # 检查是否有手动输入的数值（简单启发式）
    # 匹配 $... = 数字...$ 或 正文中独立的数字
    manual_numbers = []
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('%') or '\\newcommand' in line or '\\def' in line:
            continue
        # 简单匹配：等号后面的数字
        for match in re.finditer(r'=\s*([0-9]+\.?[0-9]*)', line):
            manual_numbers.append({"line": i, "number": match.group(1)})
    
    return {
        "has_input_params": has_input_params,
        "manual_number_count": len(manual_numbers),
    }


def numerical_pipeline_check(tex_path: Path) -> dict:
    """Run the dedicated numerical pipeline checker in strict mode."""
    script = Path(__file__).with_name("check_numerical_pipeline.py")
    if not script.exists():
        return {
            "success": False,
            "errors": [f"数值管线脚本不存在: {script}"],
            "warnings": [],
            "stdout": "",
            "stderr": "",
        }

    cmd = [sys.executable, str(script), str(tex_path), "--strict"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tex_path.parent)
    errors = []
    if result.returncode != 0:
        errors.append("check_numerical_pipeline.py --strict 未通过，存在高风险手动输入数值。")

    return {
        "success": result.returncode == 0,
        "errors": errors,
        "warnings": [],
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def compile_check(tex_path: Path, max_runs: int = 3) -> dict:
    """尝试编译，返回错误/警告信息"""
    output_dir = tex_path.parent
    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-file-line-error",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]
    
    errors = []
    warnings = []
    
    for run in range(1, max_runs + 1):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=tex_path.parent)
        log = result.stdout + result.stderr
        
        # 简单错误提取
        for line in log.split('\n'):
            if '! LaTeX Error:' in line or 'error' in line.lower():
                errors.append(line.strip())
            elif 'Warning:' in line or 'warning' in line.lower():
                warnings.append(line.strip())
        
        if result.returncode == 0 and 'Rerun to get' not in log:
            break
    
    pdf_path = output_dir / f"{tex_path.stem}.pdf"
    return {
        "success": result.returncode == 0 and pdf_path.exists(),
        "runs": run,
        "errors": list(set(errors))[:10],  # 去重，最多10个
        "warnings": list(set(warnings))[:10],
        "pdf_size_kb": round(pdf_path.stat().st_size / 1024, 1) if pdf_path.exists() else 0,
    }


def workflow_evidence_check(tex_path: Path, evidence_path: Path) -> dict:
    """运行八阶段 workflow evidence 门禁。"""
    script = Path(__file__).with_name("audit_workflow_evidence.py")
    if not script.exists():
        return {
            "success": False,
            "skipped": False,
            "errors": [f"门禁脚本不存在: {script}"],
            "warnings": [],
        }

    cmd = [
        sys.executable,
        str(script),
        str(tex_path),
        "--evidence",
        str(evidence_path),
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tex_path.parent)
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "success": False,
            "skipped": False,
            "errors": ["workflow evidence 检查输出不是有效 JSON", result.stderr.strip(), result.stdout[-1000:]],
            "warnings": [],
        }

    return {
        "success": bool(parsed.get("passed")),
        "skipped": False,
        "errors": parsed.get("errors", []),
        "warnings": parsed.get("warnings", []),
        "details": parsed.get("checks", {}),
    }


def validate(
    tex_path: Path,
    no_compile: bool = False,
    check_images_only: bool = False,
    skip_workflow_evidence: bool = False,
    evidence_path: Path | None = None,
) -> dict:
    """主编译函数"""
    report = {
        "file": str(tex_path),
        "passed": True,
        "checks": {},
    }
    
    # 1. 图片检查
    graphics = find_graphics(tex_path)
    missing_images = [g for g in graphics if not g["exists"]]
    report["checks"]["images"] = {
        "total": len(graphics),
        "missing": len(missing_images),
        "details": missing_images,
        "passed": len(missing_images) == 0,
    }
    
    if check_images_only:
        report["passed"] = report["checks"]["images"]["passed"]
        return report
    
    # 2. 数值管线检查
    params_check = check_params_tex(tex_path)
    pipeline_result = numerical_pipeline_check(tex_path)
    report["checks"]["numerical_pipeline"] = {
        "has_params_tex": params_check["has_input_params"],
        "manual_numbers_hint": params_check["manual_number_count"],
        "passed": params_check["has_input_params"] and pipeline_result["success"],
        "strict_check": pipeline_result,
    }
    
    # 3. 编译检查
    if not no_compile:
        compile_result = compile_check(tex_path)
        report["checks"]["compilation"] = compile_result
    else:
        report["checks"]["compilation"] = {"skipped": True}

    # 4. Workflow evidence 门禁
    if skip_workflow_evidence:
        report["checks"]["workflow_evidence"] = {"skipped": True}
    else:
        if evidence_path is None:
            evidence_path = tex_path.parent / "results" / "workflow_evidence.json"
        report["checks"]["workflow_evidence"] = workflow_evidence_check(tex_path, evidence_path)

    # 综合判定
    report["passed"] = (
        report["checks"]["images"]["passed"] and
        report["checks"]["numerical_pipeline"]["passed"] and
        (no_compile or report["checks"]["compilation"]["success"]) and
        (skip_workflow_evidence or report["checks"]["workflow_evidence"]["success"])
    )
    
    return report


def print_report(report: dict):
    """打印可读报告"""
    print(f"\n{'='*50}")
    print(f"📋 实验报告验证报告")
    print(f"{'='*50}")
    print(f"文件: {report['file']}")
    print(f"结果: {'✅ 通过' if report['passed'] else '❌ 未通过'}")
    
    # 图片
    img = report["checks"]["images"]
    print(f"\n📷 图片引用: {img['total']} 张", end="")
    if img["missing"] > 0:
        print(f" (❌ {img['missing']} 张缺失)")
        for m in img["details"]:
            print(f"   [{m['line']}] {m['path']}")
    else:
        print(" (全部存在)")
    
    # 数值管线
    pipe = report["checks"].get("numerical_pipeline")
    if pipe:
        print(f"\n🔢 数值管线: ", end="")
        if pipe["has_params_tex"]:
            print(f"✅ 已使用 params.tex")
        else:
            print(f"⚠️  未检测到 params.tex 引用")
        strict = pipe.get("strict_check") or {}
        if strict:
            if strict.get("success"):
                print("   ✅ 严格数值扫描通过")
            else:
                print("   ❌ 严格数值扫描未通过")
                for e in strict.get("errors", [])[:5]:
                    print(f"      {e}")
                if strict.get("stderr"):
                    print(f"      {strict['stderr']}")
    
    # 编译
    comp = report["checks"].get("compilation")
    if comp:
        if comp.get("skipped"):
            print(f"\n📝 编译检查: ⏭️  已跳过")
        else:
            print(f"\n📝 编译检查: ", end="")
            if comp["success"]:
                print(f"✅ 成功 ({comp['runs']} 次, {comp['pdf_size_kb']} KB)")
            else:
                print(f"❌ 失败")
            if comp["errors"]:
                print(f"   Errors ({len(comp['errors'])}):")
                for e in comp["errors"][:5]:
                    print(f"      {e}")
            if comp["warnings"]:
                print(f"   Warnings ({len(comp['warnings'])}):")
                for w in comp["warnings"][:5]:
                    print(f"      {w}")

    # Workflow evidence
    flow = report["checks"].get("workflow_evidence")
    if flow:
        if flow.get("skipped"):
            print(f"\n🧾 Workflow evidence: ⏭️  已跳过")
        else:
            print(f"\n🧾 Workflow evidence: ", end="")
            if flow["success"]:
                print("✅ 通过")
            else:
                print("❌ 未通过")
            if flow.get("errors"):
                print(f"   阻塞问题 ({len(flow['errors'])}):")
                for e in flow["errors"][:8]:
                    print(f"      {e}")
            if flow.get("warnings"):
                print(f"   警告 ({len(flow['warnings'])}):")
                for w in flow["warnings"][:5]:
                    print(f"      {w}")
    
    print(f"\n{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="实验报告综合验证脚本")
    parser.add_argument("tex", help="LaTeX 源文件路径")
    parser.add_argument("--no-compile", "-n", action="store_true", help="跳过编译检查")
    parser.add_argument("--check-images-only", action="store_true", help="仅检查图片")
    parser.add_argument("--evidence", help="workflow evidence JSON 路径（默认 results/workflow_evidence.json）")
    parser.add_argument("--skip-workflow-evidence", action="store_true", help="跳过八阶段 workflow evidence 门禁")
    parser.add_argument("--json", "-j", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()
    
    tex_path = Path(args.tex).resolve()
    if not tex_path.exists():
        print(f"❌ 文件不存在: {tex_path}", file=sys.stderr)
        sys.exit(1)
    
    evidence_path = None
    if args.evidence:
        raw_evidence_path = Path(args.evidence).expanduser()
        if not raw_evidence_path.is_absolute():
            raw_evidence_path = tex_path.parent / raw_evidence_path
        evidence_path = raw_evidence_path.resolve()
    report = validate(
        tex_path,
        no_compile=args.no_compile,
        check_images_only=args.check_images_only,
        skip_workflow_evidence=args.skip_workflow_evidence,
        evidence_path=evidence_path,
    )
    
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
    
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
