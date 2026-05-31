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

This skill was created from repeated AI-assisted lab-report-writing cycles and is intended to run across Codex, Claude Code, and Kimi Code. It encodes lessons learned from those cycles into a **systematic workflow** that catches errors at the source rather than after completion.

The core philosophy is **prevention over inspection**: build correctness into each stage so that late-stage review becomes confirmation, not repair.

## Target Environment

- **Primary**: Any agent that can read files, run Python/LaTeX scripts, and visually inspect rendered images
- **Known consumers**: Codex, Claude Code, Kimi Code
- **Model characteristics**: Large context and long outputs help full-report generation, but all agents can still make low-level reasoning, transcription, plotting, and copy-paste errors
- **Compensation strategy**: Process redundancy and forced validation (numerical pipeline, cross-verification, page-by-page review)

## Users

| User | How they interact |
|------|-------------------|
| Student | Provides lecture PDF, data files, and optional template path. Issues a single command. Reviews AI output and answers clarification questions. |
| AI Agent | Loads `SKILL.md`, chooses the task mode, consults `references/` as needed, asks user when uncertainty is blocking. |
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
