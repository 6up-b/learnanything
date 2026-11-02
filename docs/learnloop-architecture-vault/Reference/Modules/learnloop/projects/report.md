---
title: "learnloop.projects.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/projects/report.py"
source_paths:
  - "src/learnloop/projects/report.py"
source_commit: "e084cd25855d0dac1168e35a7c24d54bba421fd4"
source_commit_timestamp: "2026-10-12T01:16:40-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.projects"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.projects.report module"
  - "src/learnloop/projects/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-projects"
---

# `learnloop.projects.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.projects.report` exists within [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] to own the behavior summarized by its module contract: The M1 probe report (spec §8.3): are the probes valid, and are they worth it?

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/projects/report.py](../../../../../../src/learnloop/projects/report.py) |
| Source lines | 443 |
| Owning package | [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e084cd25855d0dac1168e35a7c24d54bba421fd4` |
| Commit timestamp | `2026-10-12T01:16:40-04:00` |

## Public API

- `outcome_of_record(response: dict[str, Any]) -> float | None` ([source](../../../../../../src/learnloop/projects/report.py), line 50)
- `build_report(store: ProjectStore, config: LearnLoopConfig, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/report.py), line 90)
- `render_report(report: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/projects/report.py), line 266) — A compact plain-text view of :func:`build_report`.
- `build_status(store: ProjectStore, *, clock: Clock | None=None, disclosure: bool=False, include_diffs: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/report.py), line 324) — Counts per repo.

### Module constants

- `SMALL_SAMPLE` ([src/learnloop/projects/report.py](../../../../../../src/learnloop/projects/report.py), line 30)

### Explicit exports

`__all__` declares:

- `build_report`
- `build_status`
- `outcome_of_record`
- `render_report`

## Internal implementation anchors

- `_rate(numerator: int, denominator: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/report.py), line 33)
- `_mean(values: list[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/projects/report.py), line 42)
- `_stage(receipt: dict[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/projects/report.py), line 58)
- `_cost_by_diff(receipts: list[dict[str, Any]], *, answer_grading: bool=False) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/projects/report.py), line 65) — Root-call cost per diff: generation stages, or (``answer_grading``) owner-answer grades.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `build_report`, `build_status`, `render_report`; statically calls `build_report`, `build_status`, `render_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/projects/ai_contracts|learnloop.projects.ai_contracts]] — imports `CLOSED_BOOK_PROMPT_VERSION`, `PROBE_AUTHORING_PROMPT_VERSION`, `PROBE_GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `ProjectStore`, `STORE_SCHEMA_VERSION`
- [[Reference/Modules/learnloop/projects/redaction|learnloop.projects.redaction]] — imports `SECRET_PATTERN_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_project_report.py](../../../../../../tests/test_project_report.py) — direct import
  - `test_outcome_of_record_prefers_adjudication`
  - `test_report_figures`
  - `test_status_counts_without_question_text`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.projects; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/projects/report.py](../../../../../../src/learnloop/projects/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
