#!/usr/bin/env python3
"""
通用 LaTeX 实验报告编译脚本

自动运行 xelatex 多次直到交叉引用稳定，捕获并格式化错误/警告。
支持 ctexart 文档类，自动处理中文。

用法:
    python3 compile_report.py report.tex
    python3 compile_report.py report.tex --clean      # 编译后清理辅助文件
    python3 compile_report.py report.tex --watch      # 监听文件变化自动编译（需要 watchdog）
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_xelatex(tex_file: Path, output_dir: Path) -> tuple[int, str, str]:
    """运行一次 xelatex，返回 (returncode, stdout, stderr)"""
    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-file-line-error",
        f"-output-directory={output_dir}",
        str(tex_file),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=tex_file.parent)
    return result.returncode, result.stdout, result.stderr


def parse_errors(log_text: str) -> list[dict]:
    """从 xelatex 日志中提取 error 和 warning"""
    errors = []
    warnings = []

    # Error pattern: file:line: error message
    error_pattern = re.compile(r'^(.+?):(\d+):\s*(.+)$', re.MULTILINE)
    for match in error_pattern.finditer(log_text):
        filepath, line, msg = match.groups()
        msg_stripped = msg.strip()
        if 'error' in msg_stripped.lower() or msg_stripped.startswith('!'):
            errors.append({"file": filepath, "line": int(line), "message": msg_stripped})
        elif 'warning' in msg_stripped.lower():
            warnings.append({"file": filepath, "line": int(line), "message": msg_stripped})

    # ! LaTeX Error: ... pattern
    latex_error = re.compile(r'! LaTeX Error: (.+?)(?:\n|\.\s*$)', re.MULTILINE)
    for match in latex_error.finditer(log_text):
        errors.append({"file": "unknown", "line": 0, "message": f"LaTeX Error: {match.group(1).strip()}"})

    # Package warning pattern
    pkg_warn = re.compile(r'Package (.+?) Warning: (.+?)(?: on input line (\d+))?(?:\.|$)', re.MULTILINE)
    for match in pkg_warn.finditer(log_text):
        pkg, msg, line = match.groups()
        warnings.append({"file": "unknown", "line": int(line) if line else 0, "message": f"[{pkg}] {msg.strip()}"})

    # Overfull/Underfull
    overfull = re.compile(r'(Overfull|Underfull)\\s+(\\[a-z]+).+?lines? (\d+)', re.MULTILINE)
    for match in overfull.finditer(log_text):
        warnings.append({"file": "unknown", "line": int(match.group(3)), "message": match.group(0).strip()})

    return errors, warnings


def needs_rerun(log_text: str) -> bool:
    """检查是否需要重新编译（交叉引用未稳定）"""
    rerun_indicators = [
        "Rerun to get cross-references right",
        "Rerun to get outlines right",
        "LaTeX Warning: Label(s) may have changed",
        "LaTeX Warning: There were undefined references",
        "Label(s) may have changed",
    ]
    return any(ind in log_text for ind in rerun_indicators)


def clean_aux_files(output_dir: Path, tex_stem: str):
    """清理编译辅助文件"""
    extensions = [
        '.aux', '.log', '.out', '.synctex.gz',
        '.fdb_latexmk', '.fls', '.toc', '.lof', '.lot',
        '.bbl', '.blg', '.nav', '.snm', '.vrb',
    ]
    for ext in extensions:
        f = output_dir / f"{tex_stem}{ext}"
        if f.exists():
            f.unlink()


def compile_report(tex_file: Path, max_runs: int = 5, clean: bool = False, verbose: bool = False):
    """主编译函数"""
    if not tex_file.exists():
        print(f"❌ 文件不存在: {tex_file}", file=sys.stderr)
        sys.exit(1)

    tex_stem = tex_file.stem
    output_dir = tex_file.parent
    pdf_file = output_dir / f"{tex_stem}.pdf"

    all_errors = []
    all_warnings = []
    runs = 0

    print(f"📝 编译: {tex_file.name}")

    for run in range(1, max_runs + 1):
        runs = run
        print(f"  第 {run} 次编译...", end=" ", flush=True)
        rc, stdout, stderr = run_xelatex(tex_file, output_dir)
        log_text = stdout + stderr

        errors, warnings = parse_errors(log_text)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

        if rc != 0 and not errors:
            # 非零退出码但没有解析到错误，可能是 fatal error
            print("❌ 编译失败")
            print(log_text[-2000:])  # 打印最后 2000 字符
            sys.exit(1)

        if errors:
            print("⚠️ 有错误")
            if verbose:
                for e in errors:
                    print(f"    [{e['file']}:{e['line']}] {e['message']}")
            # 有错误也继续检查是否需要重编译，但标记失败
            break

        if needs_rerun(log_text):
            print("🔄 需要重编译")
            continue

        print("✅ 完成")
        break
    else:
        print(f"⚠️ 达到最大编译次数 ({max_runs})，交叉引用可能未完全稳定")

    # 输出结果
    print()
    if pdf_file.exists():
        size = pdf_file.stat().st_size / 1024
        print(f"📄 PDF: {pdf_file} ({size:.1f} KB)")
    else:
        print(f"❌ PDF 未生成")

    if all_errors:
        print(f"\n🔴 Errors ({len(all_errors)}):")
        for e in all_errors[:10]:  # 最多显示 10 个
            print(f"   [{e['file']}:{e['line']}] {e['message']}")
        if len(all_errors) > 10:
            print(f"   ... 还有 {len(all_errors) - 10} 个")

    if all_warnings:
        print(f"\n🟡 Warnings ({len(all_warnings)}):")
        for w in all_warnings[:10]:
            print(f"   [{w['file']}:{w['line']}] {w['message']}")
        if len(all_warnings) > 10:
            print(f"   ... 还有 {len(all_warnings) - 10} 个")

    if clean:
        clean_aux_files(output_dir, tex_stem)
        print("\n🧹 辅助文件已清理")

    return len(all_errors) == 0


def main():
    parser = argparse.ArgumentParser(description="通用 LaTeX 实验报告编译脚本")
    parser.add_argument("tex_file", help="LaTeX 源文件路径")
    parser.add_argument("--max-runs", type=int, default=5, help="最大编译次数 (默认 5)")
    parser.add_argument("--clean", action="store_true", help="编译后清理辅助文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")
    args = parser.parse_args()

    tex_file = Path(args.tex_file).resolve()
    success = compile_report(tex_file, max_runs=args.max_runs, clean=args.clean, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
