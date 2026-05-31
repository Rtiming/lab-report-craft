#!/usr/bin/env python3
"""
数值管线检查脚本

扫描 LaTeX 报告源文件，识别正文中手动输入的数值（未通过数值管线），
并与 params.tex 中的宏定义对比，输出潜在不一致风险。

核心规则：正文中每个计算结果数值应来自脚本输出的唯一来源（params.tex + \newcommand）。
讲义给定的标准值、仪器参数等固定值允许手动输入（应在注释中标注来源）。

用法:
    # 检查单份报告
    python3 check_numerical_pipeline.py report.tex

    # 指定 params.tex 路径（默认自动搜索同级目录下的 results/params.tex）
    python3 check_numerical_pipeline.py report.tex --params results/params.tex

    # 宽松模式：忽略常见固定值（如光速、普朗克常数等）
    python3 check_numerical_pipeline.py report.tex --ignore-constants

    # 仅显示高风险项（未在 params.tex 中出现且非标准常数）
    python3 check_numerical_pipeline.py report.tex --strict
"""

import argparse
import re
import sys
from pathlib import Path


# 常见物理常数和仪器参数，在严格模式下可忽略
COMMON_CONSTANTS = {
    "2.998", "3.141", "6.626", "1.602", "9.109", "1.381",
    "273.15", "22.4", "8.314", "101.325", "760",
    "980", "9.8",
}


def parse_params_tex(params_path: Path) -> dict[str, str]:
    """解析 params.tex，返回 {宏名: 数值} 字典"""
    params = {}
    if not params_path.exists():
        return params

    text = params_path.read_text(encoding="utf-8")

    # \newcommand{\valJs}{0.3996}
    newcmd_pattern = re.compile(r'\\newcommand\{\\([^}]+)\}\{([^}]+)\}')
    for match in newcmd_pattern.finditer(text):
        name, value = match.groups()
        params[name] = value.strip()

    # \newcommand*{\valJs}{0.3996} (带星号版本)
    newcmd_star_pattern = re.compile(r'\\newcommand\*\{\\([^}]+)\}\{([^}]+)\}')
    for match in newcmd_star_pattern.finditer(text):
        name, value = match.groups()
        params[name] = value.strip()

    # \def\valJs{0.3996}
    def_pattern = re.compile(r'\\def\\([^\s{]+)\{([^}]+)\}')
    for match in def_pattern.finditer(text):
        name, value = match.groups()
        params[name] = value.strip()

    return params


def find_manual_numbers(tex_path: Path) -> list[dict]:
    """
    在 LaTeX 源文件中查找手动输入的数值。
    返回 [{line, col, context, number, risk_level}, ...]
    """
    text = tex_path.read_text(encoding="utf-8")
    lines = text.split('\n')
    findings = []

    # 数值模式：匹配数学环境或正文中的数字
    # 包括：$...= 123.45...$，$123.45$，文字中嵌入的数字等
    # 排除：\newcommand, \def, \label, \ref, \cite, \input 等命令内部
    # 排除：注释行

    number_pattern = re.compile(
        r'(?<![\\a-zA-Z])'  # 前面不是反斜杠或字母（排除命令参数名）
        r'(?<![\d])'         # 前面不是数字（排除多位数的一部分）
        r'(\d+\.?\d*)'       # 数字本身
        r'(?![\d])'          # 后面不是数字
    )

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        # 跳过注释行和空行
        if not stripped or stripped.startswith('%'):
            continue

        # 跳过命令定义行
        if stripped.startswith('\\newcommand') or stripped.startswith('\\def'):
            continue

        # 跳过 \input, \include 行
        if stripped.startswith('\\input') or stripped.startswith('\\include'):
            continue

        # 在行间找数值
        for match in number_pattern.finditer(line):
            num_str = match.group(1)
            col = match.start() + 1

            # 跳过 LaTeX 命令参数中的数字（如 \section{1. 引言}）
            if is_inside_latex_command(line, match.start()):
                continue

            # 跳过坐标、尺寸等（如 \includegraphics[width=0.8\textwidth]）
            if is_latex_dimension(line, match.start()):
                continue

            # 跳过科学计数法中的指数部分（如 10^{-34} 中的 10 和 34）
            if is_scientific_notation(line, match.start(), match.end()):
                continue

            # 提取上下文
            start = max(0, match.start() - 20)
            end = min(len(line), match.end() + 20)
            context = line[start:end].strip()

            findings.append({
                "line": line_no,
                "col": col,
                "number": num_str,
                "context": context,
                "risk_level": "unknown",
            })

    return findings


def is_inside_latex_command(line: str, pos: int) -> bool:
    """检查位置是否在某个 LaTeX 命令的参数括号内"""
    # 简单启发式：查找最近的 { 和 }
    before = line[:pos]
    after = line[pos:]

    # 如果在 \command{...} 中
    # 简单检查：前面有 { 且后面有 }
    last_brace_open = before.rfind('{')
    last_brace_close = before.rfind('}')
    next_brace_close = after.find('}')

    if last_brace_open > last_brace_close and next_brace_close != -1:
        # 检查前面的反斜杠命令
        cmd_start = before.rfind('\\', 0, last_brace_open)
        if cmd_start != -1:
            cmd = before[cmd_start:last_brace_open]
            # 这些是常见的包含数字的命令
            ignore_cmds = ['\\section', '\\subsection', '\\label', '\\ref',
                          '\\cite', '\\bibitem', '\\includegraphics',
                          '\\begin', '\\end', '\\setlength', '\\addtolength',
                          '\\newcommand', '\\DeclareSIUnit']
            for ic in ignore_cmds:
                if cmd.startswith(ic):
                    return True
    return False


def is_latex_dimension(line: str, pos: int) -> bool:
    """检查是否是 LaTeX 尺寸/坐标值"""
    context = line[max(0, pos-10):pos+10]
    dim_patterns = [
        r'\d+\.?\d*\s*(cm|mm|pt|em|ex|sp|bp|dd|pc|in)',
        r'\d+\.?\d*\\textwidth',
        r'\d+\.?\d*\\linewidth',
        r'\d+\.?\d*\\textheight',
        r'width=\d+\.?\d*',
        r'height=\d+\.?\d*',
        r'scale=\d+\.?\d*',
    ]
    for pat in dim_patterns:
        if re.search(pat, context):
            return True
    return False


def is_scientific_notation(line: str, start: int, end: int) -> bool:
    """
    检查当前数字是否是科学计数法的底数(10)或指数。
    避免将系数（如 6.626）误判为科学计数法的一部分。
    """
    num = line[start:end]
    after = line[end:end+8]

    # 当前数字是 10 且后面跟着 ^ → 科学计数法底数
    if num == "10" and "^" in after:
        return True

    # 当前数字在 10^{...} 或 10^-... 中 → 指数
    # 在 start 之前搜索最近的 10^
    before = line[:start]
    idx = before.rfind('10^')
    if idx != -1:
        # 检查 10^ 和当前数字之间只有 {、-、}、空格
        between = before[idx + 3:start]
        if re.match(r'^[\{\-\}\s]*$', between):
            return True

    # 当前数字前面有 e/E 和 +/- → 科学计数法指数
    before_narrow = line[max(0, start-3):start]
    if re.search(r'[eE][\+\-]?$', before_narrow):
        return True

    return False


def assess_risk(findings: list[dict], params: dict[str, str], ignore_constants: bool = False) -> list[dict]:
    """评估每个发现的风险等级"""
    param_values = set(v.strip() for v in params.values())
    param_names = set(params.keys())

    for f in findings:
        num = f["number"]

        # 如果数值在 params.tex 中，说明已走数值管线 → 低风险
        if num in param_values:
            f["risk_level"] = "low"
            f["reason"] = f"数值在 params.tex 中定义"
            continue

        # 检查是否是常见物理常数
        is_constant = any(num.startswith(cc) or cc.startswith(num) for cc in COMMON_CONSTANTS)

        if is_constant:
            if ignore_constants:
                f["risk_level"] = "low"
                f["reason"] = "常见物理常数/仪器参数"
            else:
                f["risk_level"] = "medium"
                f["reason"] = "常见物理常数/仪器参数（允许手动输入，请确认）"
        else:
            # 不是常数，也不在 params.tex 中 → 高风险（疑似手动输入计算结果）
            f["risk_level"] = "high"
            f["reason"] = "未在 params.tex 中定义，疑似手动输入计算结果"

    return findings


def print_report(findings: list[dict], params_path: Path, strict: bool = False):
    """输出检查报告"""
    if strict:
        findings = [f for f in findings if f["risk_level"] != "low"]

    high = [f for f in findings if f["risk_level"] == "high"]
    medium = [f for f in findings if f["risk_level"] == "medium"]
    low = [f for f in findings if f["risk_level"] == "low"]

    print(f"\n📊 数值管线检查报告")
    print(f"   params.tex: {params_path if params_path.exists() else '未找到'}")
    print(f"   总计发现数值: {len(findings)} 个")
    print(f"   🔴 高风险 (疑似手动输入): {len(high)} 个")
    print(f"   🟡 中风险 (未定义，可能为标准值): {len(medium)} 个")
    print(f"   🟢 低风险 (数值管线/常数): {len(low)} 个")

    if high:
        print(f"\n🔴 高风险项（建议核实是否应走数值管线）:")
        for f in high[:20]:
            print(f"   [{f['line']}:{f['col']}] {f['number']:>10s}  |  ...{f['context']}...")
        if len(high) > 20:
            print(f"   ... 还有 {len(high) - 20} 个")

    if medium and not strict:
        print(f"\n🟡 中风险项（可能是讲义给定的标准值，请确认）:")
        for f in medium[:10]:
            print(f"   [{f['line']}:{f['col']}] {f['number']:>10s}  |  ...{f['context']}...")
        if len(medium) > 10:
            print(f"   ... 还有 {len(medium) - 10} 个")

    print()
    return len(high) == 0


def main():
    parser = argparse.ArgumentParser(description="数值管线检查脚本")
    parser.add_argument("tex", help="LaTeX 源文件路径")
    parser.add_argument("--params", help="params.tex 路径（默认自动搜索）")
    parser.add_argument("--ignore-constants", "-i", action="store_true", help="忽略常见物理常数")
    parser.add_argument("--strict", "-s", action="store_true", help="仅显示高风险项")
    args = parser.parse_args()

    tex_path = Path(args.tex).resolve()
    if not tex_path.exists():
        print(f"❌ 文件不存在: {tex_path}", file=sys.stderr)
        sys.exit(1)

    # 自动搜索 params.tex
    if args.params:
        params_path = Path(args.params).resolve()
    else:
        # 常见位置：同级目录的 results/params.tex 或 params.tex
        candidates = [
            tex_path.parent / "results" / "params.tex",
            tex_path.parent / "params.tex",
            tex_path.parent.parent / "results" / "params.tex",
        ]
        params_path = next((c for c in candidates if c.exists()), candidates[0])

    params = parse_params_tex(params_path)
    findings = find_manual_numbers(tex_path)
    findings = assess_risk(findings, params, ignore_constants=args.ignore_constants)
    ok = print_report(findings, params_path, strict=args.strict)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
