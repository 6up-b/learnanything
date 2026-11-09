---
title: "learnloop.reveal_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reveal_coverage.py"
source_paths:
  - "src/learnloop/reveal_coverage.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.reveal_coverage module"
  - "src/learnloop/reveal_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.reveal_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reveal_coverage` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: How long a routine full-answer display counts as an exposure: one definition for every reader of the reveal ledger (UX Phase 4, rounds 3 and 4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py) |
| Source lines | 157 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_routine_display(source_kind: object, basis: object) -> bool` ([source](../../../../../src/learnloop/reveal_coverage.py), line 68) — Is a reveal row (its ``source_kind`` and ``basis``) a routine display?
- `routine_display_sql(table: str='') -> tuple[str, list[object]]` ([source](../../../../../src/learnloop/reveal_coverage.py), line 74) — A SQL predicate (and its parameters) true for routine display rows; a prefix match without LIKE (its "_" is a wildcard).
- `routine_covered_from(at: datetime | str) -> str | None` ([source](../../../../../src/learnloop/reveal_coverage.py), line 86) — The earliest stamp of a routine row still covering ``at`` (ledger format): rows stamped at or after it cover ``at`` (inclusive).
- `routine_row_covers(created_at: str, at: datetime | str) -> bool` ([source](../../../../../src/learnloop/reveal_coverage.py), line 95) — Does a routine row stamped ``created_at`` cover the moment ``at``?
- `routine_coverage_sql(covered_from: str, table: str='') -> tuple[str, list[object]]` ([source](../../../../../src/learnloop/reveal_coverage.py), line 104) — The convention in SQL: a predicate true for routine rows stamped at or after ``covered_from`` (``routine_covered_from(T)``, or ``routine_window_start(since)`` for a reader whose window starts at ``since = T - delay``), with no upper bound.
- `routine_released_at(created_at: str) -> str | None` ([source](../../../../../src/learnloop/reveal_coverage.py), line 115) — The first moment (ledger format) a routine row stamped ``created_at`` no longer covers: one second after its coverage ends.
- `routine_displays_covering(repository: object, *, practice_item_id: str, learning_object_id: str | None=None, at: datetime | str) -> list[dict[str, object]]` ([source](../../../../../src/learnloop/reveal_coverage.py), line 124) — The routine display rows covering ``at`` on the item (and, when ``learning_object_id`` is given, anywhere in its learning object): the one read behind every serve-time hold (UX Phase 4 round 6), a cold check's (item or learning object, the scheduler's deferral scope) and a probe…
- `routine_window_start(since: str) -> str` ([source](../../../../../src/learnloop/reveal_coverage.py), line 149) — For a reader whose window for a reveal starts at ``since`` (``T`` minus the cold retrieval delay): where its window for routine rows starts, the renewal grace earlier.

### Module constants

- `ROUTINE_DISPLAY_BASES` ([src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py), line 42)
- `ROUTINE_DISPLAY_HORIZON` ([src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py), line 46)
- `ROUTINE_DISPLAY_RENEWAL_GRACE` ([src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py), line 50)
- `ROUTINE_DISPLAY_COVERAGE` ([src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py), line 53)

## Internal implementation anchors

- `_iso(moment: datetime) -> str` ([source](../../../../../src/learnloop/reveal_coverage.py), line 56)
- `_parsed(value: str) -> datetime | None` ([source](../../../../../src/learnloop/reveal_coverage.py), line 60)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `ROUTINE_DISPLAY_BASES`, `ROUTINE_DISPLAY_COVERAGE`, `ROUTINE_DISPLAY_HORIZON`, `ROUTINE_DISPLAY_RENEWAL_GRACE`, `is_routine_display`, `routine_covered_from`; statically calls `is_routine_display`, `routine_covered_from`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `routine_coverage_sql`, `routine_window_start`; statically calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `routine_coverage_sql`, `routine_window_start`; statically calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `routine_displays_covering`; statically calls `routine_displays_covering`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `routine_coverage_sql`, `routine_window_start`; statically calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `routine_coverage_sql`, `routine_window_start`; statically calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `is_routine_display`, `routine_displays_covering`, `routine_released_at`, `routine_row_covers`; statically calls `is_routine_display`, `routine_displays_covering`, `routine_released_at`, `routine_row_covers`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `ROUTINE_DISPLAY_COVERAGE`, `is_routine_display`, `routine_covered_from`, `routine_released_at`, `routine_row_covers`; statically calls `is_routine_display`, `routine_covered_from`, `routine_released_at`, `routine_row_covers`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]], [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]], [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_serve_eligibility.py](../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_submit_exposure_is_the_sql_total_row_for_row`
- [tests/test_ux_phase4_feedback.py](../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1j_every_reader_agrees_at_the_exact_boundary_second`
  - `test_f1k_a_routine_display_hold_clears_by_itself`
- [tests/test_ux_phase4_landing.py](../../../../../tests/test_ux_phase4_landing.py) — direct import
  - `test_a_routine_display_marks_a_later_question_solution_seen_beyond_its_coverage`

## Modification guidance

- Make changes here when the responsibility remains reveal coverage within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reveal_coverage.py](../../../../../src/learnloop/reveal_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
