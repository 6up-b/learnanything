---
title: "learnloop.hints.report_workbench"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/report_workbench.py"
source_paths:
  - "src/learnloop/hints/report_workbench.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.report_workbench module"
  - "src/learnloop/hints/report_workbench.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.report_workbench`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.report_workbench` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Reader workbench RW2b: the workbench rows of ``learnloop hints report`` (spec_reader_workbench_v1 §13 RW2b checkpoint, §15; UX §9.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/report_workbench.py](../../../../../../src/learnloop/hints/report_workbench.py) |
| Source lines | 463 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `build_workbench_report(sqlite_path: Path | str, *, item_facets: Mapping[str, Iterable[str]] | None=None, since: str | None=None, symbolic_enabled: bool=False) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 77) — The workbench block, or None when the vault has no workbench rows.
- `workbench_unaided_progress(row: Mapping[str, Any], session_rows: Iterable[Mapping[str, Any]], *, maps: Mapping[str, Mapping[str, list[str]]] | None=None) -> str` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 275) — Unaided next progress for one shown workbench help row (§6.1: "in the workbench, progress ...

### Module constants

- `REPORT_VERSION` ([src/learnloop/hints/report_workbench.py](../../../../../../src/learnloop/hints/report_workbench.py), line 38)
- `WORKBENCH_HELP_KINDS` ([src/learnloop/hints/report_workbench.py](../../../../../../src/learnloop/hints/report_workbench.py), line 253)
- `PROGRESS_OUTCOMES` ([src/learnloop/hints/report_workbench.py](../../../../../../src/learnloop/hints/report_workbench.py), line 255)

### Explicit exports

`__all__` declares:

- `PROGRESS_OUTCOMES`
- `REPORT_VERSION`
- `WORKBENCH_HELP_KINDS`
- `build_workbench_report`
- `workbench_unaided_progress`

## Internal implementation anchors

- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 41)
- `_when(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 48)
- `_percentiles(values: Iterable[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 58)
- `_week(value: Any) -> str` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 69)
- `_snapshot_pairs(value: Any) -> set[tuple[str, str]] | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 258) — A row's ``step_snapshot_json`` as ``(chain_id, content hash)`` pairs, or None when the row recorded none (the work at delivery is unknown).
- `_parent(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 269)
- `_last_check_verdicts(rows: Iterable[Mapping[str, Any]], before: datetime | None, at: Any) -> list[dict[str, Any]] | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 367) — The verdicts of the problem's last shown check at or before ``before``.
- `_valid_at_delivery(row: Mapping[str, Any], head_row: Mapping[str, Any] | None, rows: Iterable[Mapping[str, Any]], at: Any) -> set[str] | None` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 379) — The chains valid when the help was delivered (fix round 3, M1), or None when nothing records it: * the row's own ``step_verdicts_json`` (a hint's request context; a worked example stores the verdicts it was searched against); * a hint without one: the problem's last shown check…
- `_positions(value: Any) -> dict[str, int]` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 412)
- `_progress_at_placement(placed: Mapping[str, Any], snapshot_row: Mapping[str, Any], delivered: set[tuple[str, str]], following: Mapping[str, Any], maps: Mapping[str, Mapping[str, list[str]]], *, valid_then: set[str]) -> bool` ([source](../../../../../../src/learnloop/hints/report_workbench.py), line 424) — Whether the next check found progress where the help was placed (:func:`workbench_unaided_progress`, fix round 2, 6).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]] — imports `build_workbench_report`; statically calls `build_workbench_report`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `workbench_unaided_progress`; statically calls `workbench_unaided_progress`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/hints/report_adaptive|learnloop.hints.report_adaptive]] — imports `module`; calls `hint_target`, `progress_by_next_placement`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `has_verdict_record`, `symbolic_outcomes`, `verdict_records`; calls `has_verdict_record`, `symbolic_outcomes`, `verdict_records`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]], [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — direct import
  - `test_f6_hint_then_figure_then_check_is_more_help_not_unaided_progress`
- [tests/test_reader_rw2b_fix10.py](../../../../../../tests/test_reader_rw2b_fix10.py) — direct import
  - `test_item1_enable_check_disable_then_resume_recheck_hint_and_report_never_read_checked`
- [tests/test_reader_rw2b_fix14.py](../../../../../../tests/test_reader_rw2b_fix14.py) — direct import
  - `test_items_2_3_a_row_stored_checked_reads_as_the_models_everywhere_once_the_switch_is_off`
- [tests/test_reader_rw2b_fix9.py](../../../../../../tests/test_reader_rw2b_fix9.py) — direct import
  - `test_the_workbench_report_counts_no_checked_verdict`
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_m1_a_show_me_example_reads_its_own_verdicts_or_the_last_check_before_it`
  - `test_m1_a_show_me_example_with_no_verdicts_on_record_is_unknown_never_continued`
- [tests/test_workbench_report.py](../../../../../../tests/test_workbench_report.py) — direct import
  - `test_the_block_counts_checks_rungs_replies_and_questions_and_never_the_text`

## Modification guidance

- Make changes here when the responsibility remains report workbench within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/report_workbench.py](../../../../../../src/learnloop/hints/report_workbench.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
