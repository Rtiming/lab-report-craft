# Troubleshooting

## Compilation Failures

### `! LaTeX Error: File 'ctexart.cls' not found`
**Cause**: Missing Chinese LaTeX support.  
**Check**: `xelatex --version`  
**Fix**: Install TeX Live full or `texlive-lang-chinese` package. On macOS: `brew install --cask mactex` or `brew install mactex-no-gui`.

### `! Undefined control sequence \valJs`
**Cause**: `params.tex` not loaded, or macro name mismatch.  
**Check**: Does `report.tex` contain `\input{results/params.tex}`? Does `params.tex` define `\valJs`?  
**Fix**: Verify path and macro names. Run `check_numerical_pipeline.py` to find unmapped values.

### `Overfull \hbox` warnings everywhere
**Cause**: Chinese text line-breaking difficulty or oversized tables/figures.  
**Check**: `references/practical-guide.md` §3.1 已配置 `\tolerance=1200` 和 `\emergencystretch=3em`。  
**Fix**: Reduce figure width (`width=0.85\textwidth` → `0.75`), shrink table font, or allow line breaks in long formulae.

### Compilation hangs / infinite loop
**Cause**: Cross-reference instability (e.g., forward reference in page header).  
**Fix**: `compile_report.py` already limits to 5 runs. If it still hangs, check for `\pageref` inside floating environments.

## Figure Quality Issues

### Parameter box shows `$J_s=...~\mathrm{emu}$$` as literal text
**Cause**: matplotlib mathtext `$$` + `\n` crash.  
**Fix**: Use single `$` per line, separated by `\n`. See `references/practical-guide.md` §2.5.  
**Verification**: Run `pdf_to_png.py figure.pdf` and open the PNG to confirm.

### Parameter box overlaps data points
**Cause**: Default position conflicts with data range.  
**Check**: `references/practical-guide.md` §2.3 避障检查清单。  
**Fix**: Move to `upper left`, `lower left`, or outside axes via `bbox_to_anchor`.

### Extracted figure from PDF has black background
**Cause**: PDF embedded image contains transparency; LaTeX white background makes it appear black.  
**Fix**: `extract_figures_from_pdf.py` auto-converts transparent RGBA → white-background RGB. If manually extracting, use PIL: `Image.new("RGB", img.size, (255,255,255)).paste(img, mask=img.split()[3])`.

## Data Processing Issues

### Handwritten data OCR gives `6.234` but original is `0.234`
**Cause**: 0↔6 misrecognition.  
**Check**: `references/practical-guide.md` §1.4 易混淆字符清单。  
**Fix**: Always use two independent OCR methods + manual spot-check. Ask user to confirm ambiguous digits. **Never proceed with unverified handwritten data.**

### Fitted parameter sign is wrong (negative lifetime, negative amplitude)
**Cause**: Wrong model choice or insufficient data range for fit.  
**Check**: Does the lecture specify the model? Is the initial guess reasonable?  
**Fix**: Ask user to choose model if lecture is ambiguous. Document the chosen model and its limitations in the report.

### Values in text disagree with values in figure
**Cause**: Manual copy-paste error or outdated script output.  
**Check**: Run `check_numerical_pipeline.py report.tex`.  
**Fix**: Enforce numerical pipeline (`params.tex` + `\newcommand`). Delete all manually typed computed values from the report body.

## Agent Behavior Issues

### Agent skips the "ask user" step and makes assumptions
**Cause**: `SKILL.md` or `references/ask-user-guide.md` not loaded.  
**Fix**: Ensure `SKILL.md` is in context. The uncertain-question rule is a hard boundary.

### Agent generates generic schematics with matplotlib instead of extracting from lecture
**Cause**: Agent missed the "no self-drawn schematics" rule.  
**Fix**: Point to `AGENTS.md` Hard Boundary #5. Rerun figure extraction from lecture PDF.

### Agent proofreads only text, ignoring figures
**Cause**: Agent did not execute the page-by-page figure review checklist.  
**Fix**: Enforce `references/checklist.md` §三 (逐页逐图逐句检查). Every figure must be converted to PNG and opened with `当前 agent 可用的图像查看工具`.
