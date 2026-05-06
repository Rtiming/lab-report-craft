# AGENTS.md — Lab Report Craft

Agent entry point for the `lab-report-craft` skill repository.

## First Five Minutes

1. Read `SKILL.md` for the canonical skill spec (eight-stage workflow, core principles).
2. Read `README.md` for the human-facing summary and quick-start.
3. If the task is editing a specific stage, read the matching file under `references/`.
4. If the task involves scripts (compilation, figure extraction, validation), read `assets/scripts/`.

**Do not** read the entire `references/` tree at once. It is ~2000 lines. Load only the file relevant to the current stage.

## Workspace Intent

This repository is a **Kimi Code skill** for writing university physics/engineering lab reports in Chinese, using LaTeX (`ctexart`).

It is **not** a library or application. It is a workflow specification + reference material + reusable scripts. The consumer is an AI agent (Kimi Code) executing the eight-stage workflow, not an end-user running code directly.

### Directory Ownership

| Directory | Owner | Contains |
|-----------|-------|----------|
| `SKILL.md` | Skill spec | Top-level workflow, principles, quick index. Loaded automatically by Kimi Code. |
| `references/workflow.md` | Stage details | Full eight-stage breakdown + 16 question-trigger templates. |
| `references/checklist.md` | Quality gates | Writing self-checks, seven-dimension audit, page-by-page review, teacher review. |
| `references/practical-guide.md` | Cookbook | Data processing code, visualization patterns, LaTeX recipes, figure extraction, OCR. |
| `references/ask-user-guide.md` | Question templates | When and how to ask the user for clarification. |
| `assets/template.tex` | LaTeX template | Generic `ctexart` report template. Copied per-project. |
| `assets/scripts/` | Utilities | `compile_report.py`, `pdf_to_png.py`, `extract_figures_from_pdf.py`, `check_numerical_pipeline.py`, `validate_report.py`. |

## Documentation Map

| Question | Read |
|----------|------|
| "What is this skill?" | `README.md` |
| "What are the eight stages?" | `SKILL.md` §八阶段工作流 |
| "How do I execute stage 3 (data processing)?" | `references/workflow.md` §阶段3 |
| "How do I write the param box without overlapping data?" | `references/practical-guide.md` §2.3 |
| "What checks must I run before delivery?" | `references/checklist.md` |
| "When must I ask the user instead of deciding myself?" | `references/ask-user-guide.md` |
| "How do I compile the LaTeX report?" | `assets/scripts/compile_report.py --help` |
| "How do I extract figures from the lecture PDF?" | `assets/scripts/extract_figures_from_pdf.py --help` |

## Hard Boundaries

1. **No experiment-specific content in skill files.** The skill must remain generic. Do not add formulas, parameters, or instrument names specific to a single experiment (e.g., VSM, muon lifetime) into `SKILL.md`, `references/*.md`, or `assets/template.tex`. Those belong in the per-project report, not the skill.
2. **No manual numeric input in report body.** Every computed value must flow through the numerical pipeline (`params.tex` + `\newcommand`). Enforce this in `references/practical-guide.md` and `references/checklist.md`.
3. **No matplotlib figure without post-generation validation.** Every plot must be converted to PNG and visually inspected for garbled math, overlaps, or truncation. Never rely on PDF thumbnail alone.
4. **No handwritten data without cross-verification.** At least two independent methods must confirm handwritten digits. Ambiguous characters (0↔6, 1↔7, decimal points) must be flagged to the user.
5. **No figure drawn from scratch.** Schematic diagrams must come from authoritative sources (lecture notes, textbooks, PDG/CODATA). Self-drawn matplotlib/TikZ schematics are prohibited.

## Editing Rules

- **Dirty worktree**: Run `git status` before editing. Commit unrelated changes first.
- **Generated files**: Do not commit `.DS_Store`, `*.aux`, `*.log`, `*.pdf` (report outputs), `__pycache__/`, or per-project `results/` directories. These are already in `.gitignore`.
- **Style**: Match existing Markdown style. Use Chinese for human-facing docs, English for code comments.
- **Cross-references**: When adding a new script, update `references/practical-guide.md` §5 (quick command index) and the relevant stage section in `SKILL.md`.
- **Testing**: Every new script must be run against real data before commit. Prefer existing experiment data in `~/Documents/26春大雾/` for validation.

## Validation Matrix

| Change Type | Smallest Validation |
|-------------|---------------------|
| Edit `SKILL.md` or `references/*.md` | Read the changed sections; verify cross-references resolve. |
| Edit `assets/template.tex` | Compile with `assets/scripts/compile_report.py` against a real `.tex` file. |
| Add/edit script in `assets/scripts/` | Run the script with `--help`, then against real data. See script docstrings for test commands. |
| Reorganize file structure | Run `python3 ~/.codex/skills/project-documenter/scripts/audit_project_docs.py --root .` and verify no broken links. |

## Generated / Local Data Policy

**Do not commit**:
- `.DS_Store`
- LaTeX auxiliary files (`*.aux`, `*.log`, `*.out`, `*.synctex.gz`, etc.)
- Compiled PDFs (report outputs, not the skill assets)
- Python `__pycache__/` and `*.pyc`
- Per-project `results/` directories containing data or `params.tex`
- Test outputs from `assets/scripts/` runs

**Do commit**:
- `README.md`, `AGENTS.md`, `SKILL.md`, `LICENSE`
- `references/*.md`
- `assets/template.tex`
- `assets/scripts/*.py` (after testing)
- `.gitignore`
