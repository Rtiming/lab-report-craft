# Project Context

## Background

University physics and engineering lab reports in China ("大雾实验" — foundational physics experiments) follow a highly standardized format: purpose, principle, apparatus, procedure, data processing, results, and discussion. The template is fixed, but the content changes per experiment.

Students write many of these reports. The work is repetitive yet error-prone:
- Misreading lecture requirements
- Data processing methods diverging from the lecture notes
- Manual numeric entry causing figure/text/table inconsistency
- Garbled math in matplotlib parameter boxes (mathtext + `$$` + newline crashes)
- Handwritten data misread by OCR (0→6, 1→7, decimal point shifts)
- Perfunctory proofreading that checks text but not figure rendering

## Why This Skill Exists

This skill was created and validated in the Kimi Code environment. It encodes lessons learned from repeated report-writing cycles into a **systematic workflow** that catches errors at the source rather than after completion.

The core philosophy is **prevention over inspection**: build correctness into each stage so that late-stage review becomes confirmation, not repair.

## Target Environment

- **Primary**: Kimi Code (long-output, low-cost LLM environment)
- **Model characteristics**: Large per-generation token budget, sufficient context for full lecture + all data + multi-round review, but occasional low-level reasoning and coding errors
- **Compensation strategy**: Process redundancy and forced validation (numerical pipeline, cross-verification, page-by-page review)

## Users

| User | How they interact |
|------|-------------------|
| Student | Provides lecture PDF, data files, and optional template path. Issues a single command. Reviews AI output and answers clarification questions. |
| AI Agent (Kimi Code) | Loads `SKILL.md`, executes eight-stage workflow, consults `references/` as needed, asks user when uncertain. |
| Future maintainer | Edits skill files to improve workflow, add scripts, or fix patterns. Reads `AGENTS.md` first. |

## Success Criteria

A successful report:
1. Satisfies every hard requirement in the lecture notes
2. Contains zero manually entered computed values (all via numerical pipeline)
3. Has every figure verified by direct PNG inspection (no garbled text, no overlap, no truncation)
4. Has handwritten data confirmed by at least two independent methods
5. Passes seven-dimension audit + page-by-page review + independent teacher review
6. Compiles without errors

## Scope Boundaries

- **In scope**: Generic workflow, data processing patterns, visualization guidelines, LaTeX recipes, quality checklists, reusable scripts
- **Out of scope**: Experiment-specific formulas, instrument parameters, physical constants, sample data. These belong in the per-project report, not the skill.
