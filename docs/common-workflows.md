# Common Workflows

## Workflow 0: Choose Task Mode

Before executing, classify the request:

| User intent | Mode |
|-------------|------|
| Generate a complete report from lecture notes and data | `full-report` |
| Submit or final-check a PDF | `final-submit` |
| Fix a compile error or local defect | `repair-only` |
| Extract or inspect figures | `figure-only` |
| Review quality without rewriting | `audit-only` |

Only `final-submit` requires all delivery gates. For targeted repair, run the smallest check set that proves the change.

## Workflow 1: Generate a Lab Report from Scratch

The most common use case. Student provides lecture notes and data; AI executes the full pipeline.

```
Student: "实验讲义在 lecture.pdf，数据在 data/，按模板生成实验报告。"
```

Agent execution:
1. Load `SKILL.md` → understand eight-stage framework
2. Stage 1: Read `lecture.pdf`, extract 《实验要求清单》
3. Stage 2: Read data files, cross-verify handwritten records
4. Stage 3: Process data per lecture requirements, write `results/params.tex`
5. Stage 4: Generate figures, validate each with `pdf_to_png.py`
6. Stage 5: Extract schematics from `lecture.pdf` using `extract_figures_from_pdf.py`
7. Stage 6: Write LaTeX report using `assets/template.tex`, inject values via `\input{results/params.tex}`
8. Stage 7: Create/update `results/workflow_evidence.json`, run self review and teacher review
9. Stage 8: Run `validate_report.py` and `compile_report.py --clean`, deliver PDF only after both pass

## Workflow 2: Fix a Compilation Error

```
Student: "编译报错了，帮我看看。"
```

Agent execution:
1. Run `compile_report.py report.tex --verbose`
2. Parse formatted error output
3. Fix source (missing package, broken reference, figure path error, etc.)
4. Re-run `compile_report.py` until clean
5. If error persists, ask user for lecture requirements that might clarify the missing content

## Workflow 3: Extract Figures from Lecture PDF

```
Student: "帮我提取讲义里的原理图。"
```

Agent execution:
1. Run `extract_figures_from_pdf.py lecture.pdf -o assets/extracted/`
2. Review extracted images for completeness (no truncation, no missing labels)
3. If embedded images are low quality, use `--page N --crop` to screenshot the figure region
4. Verify transparent-channel handling (white background check)

## Workflow 4: Audit Numerical Consistency

```
Student: "帮我检查一下正文里的数字和图里的是否一致。"
```

Agent execution:
1. Run `check_numerical_pipeline.py report.tex --params results/params.tex`
2. Review high-risk items (values not in `params.tex` and not common constants)
3. For each high-risk item, trace back to data processing script
4. Either move the value into `params.tex` or confirm it is a lecture-given constant with source annotation

## Workflow 5: Validate Before Submission

Pre-submission sanity check. Run in order:

```bash
# 1. Check all referenced figures exist
python3 scripts/validate_report.py report.tex --check-images-only

# 2. Check numerical pipeline integrity
python3 scripts/check_numerical_pipeline.py report.tex

# 3. Compile and review errors/warnings
python3 scripts/compile_report.py report.tex --verbose

# 4. Convert all PDF figures to PNG for visual inspection
for f in figures/*.pdf; do
    python3 scripts/pdf_to_png.py "$f"
done

# 5. Check eight-stage evidence before delivery
python3 scripts/audit_workflow_evidence.py report.tex

# 6. Full validation (includes workflow evidence)
python3 scripts/validate_report.py report.tex
```

## Workflow 6: Add a New Reusable Script

Contributor adds a utility script to `scripts/`.

1. Write script with argparse CLI, docstring, and error handling
2. Test with `--help`, then against a small fixture or real experiment data
3. Update `references/practical-guide.md` §5 (quick command index)
4. Update relevant stage section in `SKILL.md` if the script automates a stage task
5. Add execution permission: `chmod +x scripts/new_script.py`
6. Run `git add` and commit
