---
title: "learnloop.db.stores.diagnosis_review"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/diagnosis_review.py"
source_paths:
  - "src/learnloop/db/stores/diagnosis_review.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.db.stores.diagnosis_review module"
  - "src/learnloop/db/stores/diagnosis_review.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.diagnosis_review`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.diagnosis_review` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Scratch-only tables for the Slice 1 M1 offline diagnosis review.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py) |
| Source lines | 392 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class NotAScratchDatabase(RuntimeError)` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 213) — A review write was attempted outside a review scratch copy.
- `ensure_review_schema(connection: sqlite3.Connection, *, run_id: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 221) — Create the review tables and mark this database as a review scratch copy.
- `is_scratch(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 232)
- `assert_scratch(connection: sqlite3.Connection) -> None` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 241)
- `insert_review_row(connection: sqlite3.Connection, table: str, values: Mapping[str, Any], *, or_ignore: bool=False, or_replace: bool=False) -> str` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 261) — Insert one row (an ``id`` is minted when absent); returns the id.
- `update_run(connection: sqlite3.Connection, run_id: str, *, status: str | None=None, manifest: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 296)
- `update_target_positions(connection: sqlite3.Connection, positions: Mapping[str, int]) -> None` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 316) — Reorder targets (planted cases are interleaved among real ones).
- `update_spot_check_session(connection: sqlite3.Connection, session_id: str, *, position: int, finished: bool=False) -> None` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 326)
- `review_rows(connection: sqlite3.Connection, table: str, *, where: Mapping[str, Any] | None=None, order_by: str='rowid') -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 352) — Read rows with JSON columns decoded (``x_json`` also appears as ``x``).

### Module constants

- `REVIEW_SCHEMA_VERSION` ([src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 21)
- `_DDL` ([src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 23)
- `_JSON_SUFFIX` ([src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 196)
- `_TABLES` ([src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 197)

### Explicit exports

`__all__` declares:

- `NotAScratchDatabase`
- `REVIEW_SCHEMA_VERSION`
- `assert_scratch`
- `ensure_review_schema`
- `insert_review_row`
- `is_scratch`
- `review_rows`
- `update_run`
- `update_spot_check_session`
- `update_target_positions`

## Internal implementation anchors

- `_now() -> str` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 217)
- `_encode(table: str, values: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 246)
- `_decode(row: sqlite3.Row | tuple, columns: Iterable[str]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/diagnosis_review.py), line 341)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `review_rows`; statically calls `review_rows`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `review_rows`; statically calls `review_rows`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `ensure_review_schema`, `insert_review_row`, `review_rows`, `update_run`, `update_target_positions`; statically calls `ensure_review_schema`, `insert_review_row`, `review_rows`, `update_run`, `update_target_positions`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `insert_review_row`, `review_rows`, `update_spot_check_session`; statically calls `insert_review_row`, `review_rows`, `update_spot_check_session`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `review_rows`; statically calls `review_rows`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `sqlite3`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]], [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]], [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]], [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/recurrence_fakes.py](../../../../../../../tests/recurrence_fakes.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/diagnosis_review.py](../../../../../../../src/learnloop/db/stores/diagnosis_review.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
