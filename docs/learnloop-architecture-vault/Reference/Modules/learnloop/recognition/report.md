---
title: "learnloop.recognition.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/recognition/report.py"
source_paths:
  - "src/learnloop/recognition/report.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.recognition"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.recognition.report module"
  - "src/learnloop/recognition/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-recognition"
---

# `learnloop.recognition.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.recognition.report` exists within [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] to own the behavior summarized by its module contract: RE0 §4.2: the section of ``learnloop data-capture report`` that splits results by cue.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py) |
| Source lines | 141 |
| Owning package | [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `warmth_window_hours() -> float` ([source](../../../../../../src/learnloop/recognition/report.py), line 53) — The warmth window: the outcome contract's retention minimum, the delay under which a read is not a delayed one (``RETENTION_MIN_DELAY_SECONDS``, 24 hours).
- `section(connection: sqlite3.Connection, vault: Any, repository: Any, *, window_hours: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/recognition/report.py), line 64) — The cue split (module docstring).
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/recognition/report.py), line 128) — The plain-text section.

### Module constants

- `REPORT_VERSION` ([src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py), line 23)
- `OBSERVATIONAL` ([src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py), line 24)
- `EXAM_TYPES` ([src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py), line 26)
- `METHOD_SELECTION` ([src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py), line 27)
- `ACTIVE_LABEL` ([src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py), line 28)

## Internal implementation anchors

- `_cell(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/recognition/report.py), line 32)
- `_split(rows: Sequence[Mapping[str, Any]], labels: Mapping[str, C.AttemptCue]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/recognition/report.py), line 46)
- `_cells(name: str, cells: Mapping[str, Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/recognition/report.py), line 116)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `lines`, `section`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `RETENTION_MIN_DELAY_SECONDS`
- [[Reference/Modules/learnloop/recognition/cue|learnloop.recognition.cue]] — imports `module`; calls `cues`
- [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]] — imports `module`; calls `attempt_rows`, `build`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import
  - `test_an_attempt_with_an_unreadable_cue_stays_out_of_the_uncued_mean`
  - `test_the_capture_report_carries_the_section_and_stays_read_only`
  - `test_the_report_reads_imported_exam_answers_as_unlabelled_goal_date_reads`
  - `test_the_report_splits_method_selection_by_cue_reports_missing_and_never_imputes`
  - `test_the_warmth_window_is_the_outcome_contracts_retention_minimum_not_a_new_constant`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.recognition; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/recognition/report.py](../../../../../../src/learnloop/recognition/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
