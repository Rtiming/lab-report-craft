# Lab Report Craft

[![Version](https://img.shields.io/badge/version-v1.1.0--test.1-orange)](#versioning)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/agent-Codex%20%7C%20Claude%20Code%20%7C%20Kimi%20Code-2ea44f)](#agent-integration)

An AI-agent skill for producing rigorous Chinese scientific lab reports with reproducible data analysis, LaTeX output, figure QA, and final submission gates.

这个项目面向 Codex、Claude Code、Kimi Code 等 AI agent，适用于大学物理、近代物理、工程实验等中文实验报告场景。它不是一个“报告模板合集”，而是一套可执行的工作流：先读讲义、再审数据、用脚本生成结果、用 LaTeX 引用数值、逐图视觉检查，最后用门禁脚本确认报告是否可以提交。

## Why This Skill

实验报告最容易出错的地方通常不是文字不够多，而是这些问题：

- 讲义要求没被完整执行
- 数据和正文、表格、图中参数不一致
- 拟合结果被手动复制后悄悄出错
- PDF 图表缩略图看着正常，实际打开后图例、参数框或中文字体有问题
- 最终提交前缺少系统性审校证据

Lab Report Craft 把这些风险拆成明确步骤和脚本检查，让 AI agent 在写报告时留下可验证证据，而不是只给出“已检查”的口头结论。

## Highlights

- **Lecture-driven workflow**: extract experiment requirements before touching data.
- **Reproducible numerical pipeline**: generate `results/params.tex` from scripts and reference values from LaTeX macros.
- **Figure-first QA**: convert PDF figures/pages to PNG and inspect actual rendered output.
- **Cross-agent design**: works as a generic skill for Codex, Claude Code, and Kimi Code.
- **Submission gates**: validate image paths, numerical provenance, LaTeX compilation, workflow evidence, and review status.
- **Repair-friendly modes**: supports full reports, final submission checks, local repairs, figure-only work, and audits.

## Suitable Tasks

- Write or improve a Chinese physics/engineering lab report.
- Process experimental data and generate publication-quality plots.
- Fit experimental data to physical models and compare with accepted values.
- Build `ctexart` LaTeX reports with formulas, tables, figures, and Chinese text.
- Fix LaTeX compilation issues, missing figures, overlapping legends, parameter boxes, and layout defects.
- Audit whether a report satisfies the original lab instruction sheet.

## Install

Use a shared local source folder:

```bash
mkdir -p ~/.ai-skills
git clone https://github.com/Rtiming/lab-report-craft.git ~/.ai-skills/lab-report-craft
```

Then link it into the agents you use:

```bash
# Codex
mkdir -p ~/.codex/skills
ln -sfn ~/.ai-skills/lab-report-craft ~/.codex/skills/lab-report-craft

# Claude Code
mkdir -p ~/.claude/skills ~/.claude/commands
ln -sfn ~/.ai-skills/lab-report-craft ~/.claude/skills/lab-report-craft
ln -sfn ~/.ai-skills/lab-report-craft/SKILL.md ~/.claude/commands/lab-report-craft.md

# Kimi Code
mkdir -p ~/.kimi/skills
ln -sfn ~/.ai-skills/lab-report-craft ~/.kimi/skills/lab-report-craft
```

If you already maintain a central skill folder, keep this repository as the single source of truth and symlink from each agent-specific directory.

## Agent Integration

| Agent | Suggested path |
|-------|----------------|
| Codex | `~/.codex/skills/lab-report-craft` |
| Claude Code | `~/.claude/skills/lab-report-craft` |
| Claude command shortcut | `~/.claude/commands/lab-report-craft.md` |
| Kimi Code | `~/.kimi/skills/lab-report-craft` |
| Shared source | `~/.ai-skills/lab-report-craft` |

After installation, ask the agent to use `lab-report-craft` for Chinese scientific lab reports, data analysis, figure QA, LaTeX report generation, or final submission checks.

## Task Modes

| Mode | When to use | Expected checks |
|------|-------------|-----------------|
| `full-report` | Generate a complete report from instructions and data | Run the full stage 0-8 workflow |
| `final-submit` | Prepare a final PDF for submission | Compile, strict numerical check, workflow evidence, full validation |
| `repair-only` | Fix a local issue such as compilation, one figure, or one section | Run only checks related to the changed scope |
| `figure-only` | Extract, generate, or inspect figures | Convert to PNG and visually inspect the actual output |
| `audit-only` | Review an existing report | Select checks based on the audit goal |

The skill should not force final-submission gates for small repair tasks. It should still state what final checks remain unrun.

## Repository Layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | Main agent entrypoint and compact workflow instructions |
| `references/workflow.md` | Detailed eight-stage workflow and rework rules |
| `references/checklist.md` | Self-checks, page/figure/sentence review, teacher-review criteria |
| `references/practical-guide.md` | Data processing, plotting, LaTeX, PDF/image handling |
| `references/ask-user-guide.md` | Blocking vs preference-level uncertainty prompts |
| `assets/template.tex` | Generic `ctexart` lab report template |
| `scripts/compile_report.py` | Multi-run XeLaTeX compilation helper |
| `scripts/pdf_to_png.py` | Convert PDF pages/figures to PNG for visual QA |
| `scripts/extract_figures_from_pdf.py` | Extract embedded images or page screenshots from PDF files |
| `scripts/check_numerical_pipeline.py` | Detect high-risk manually typed result numbers |
| `scripts/audit_workflow_evidence.py` | Validate stage evidence, figure checks, unresolved issues, teacher review |
| `scripts/validate_report.py` | Combined validation for images, numerical pipeline, compilation, and evidence |

## Quick Start

Create a report from the template:

```bash
cp ~/.ai-skills/lab-report-craft/assets/template.tex report.tex
python3 ~/.ai-skills/lab-report-craft/scripts/audit_workflow_evidence.py --init report.tex
```

Compile the report:

```bash
python3 ~/.ai-skills/lab-report-craft/scripts/compile_report.py report.tex --verbose
```

Run final validation:

```bash
python3 ~/.ai-skills/lab-report-craft/scripts/validate_report.py report.tex
```

For local repair tasks:

```bash
# Check only image references
python3 ~/.ai-skills/lab-report-craft/scripts/validate_report.py report.tex --check-images-only

# Check numerical provenance
python3 ~/.ai-skills/lab-report-craft/scripts/check_numerical_pipeline.py report.tex --params results/params.tex --strict

# Render a figure or report page for visual inspection
python3 ~/.ai-skills/lab-report-craft/scripts/pdf_to_png.py figures/result.pdf -o checks/
python3 ~/.ai-skills/lab-report-craft/scripts/pdf_to_png.py report.pdf --all-pages -o checks/
```

## Quality Gates

Final submission should pass these gates:

1. **Requirement coverage**: the report follows the original lab instruction sheet.
2. **Data review**: raw data, units, outliers, and handwritten records have been checked.
3. **Numerical provenance**: final values come from scripts and `params.tex`, not manual copying.
4. **Figure QA**: generated PDFs are rendered to PNG and visually inspected.
5. **LaTeX build**: XeLaTeX compiles successfully with stable references.
6. **Workflow evidence**: `workflow_evidence.json` records stage completion, figure checks, unresolved issues, and review status.

## Requirements

Recommended environment:

- Python 3.10+
- `numpy`, `scipy`, `matplotlib`, `pandas`
- `PyMuPDF` (`fitz`) and `Pillow`
- XeLaTeX with `ctexart` support
- Optional: `pdftotext` for PDF text extraction

Each script supports `--help`:

```bash
python3 ~/.ai-skills/lab-report-craft/scripts/validate_report.py --help
```

## Versioning

| Version | Status | Notes |
|---------|--------|-------|
| `v1.0` | Stable baseline | Original public skill with core workflow, references, scripts, and project docs |
| `v1.1.0-test.1` | Test release | Cross-agent wording, top-level `scripts/`, task modes, stricter validation, expanded README |

The current branch tracks the test release. Use `v1.0` if you want the earlier stable baseline.

## Maintenance

- Keep `SKILL.md` compact and agent-oriented.
- Put deterministic helpers in `scripts/`.
- Put detailed operational guidance in `references/`.
- Keep templates and reusable output assets in `assets/`.
- Do not commit generated PDFs, LaTeX auxiliary files, `results/`, build outputs, or `__pycache__/`.
- Run at least `python3 -m py_compile scripts/*.py` and the skill validator before publishing changes.

## License

MIT. See [LICENSE](LICENSE).
