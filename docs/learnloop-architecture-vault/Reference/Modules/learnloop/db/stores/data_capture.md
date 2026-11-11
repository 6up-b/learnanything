---
title: "learnloop.db.stores.data_capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/data_capture.py"
source_paths:
  - "src/learnloop/db/stores/data_capture.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.data_capture module"
  - "src/learnloop/db/stores/data_capture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.data_capture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.data_capture` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Data capture's append-only records (migration 240).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py) |
| Source lines | 268 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `receipts_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 52)
- `objectives_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 56)
- `insert_prefilter_receipt(connection: sqlite3.Connection, row: Mapping[str, Any], parts: Mapping[str, tuple[str, str]]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 60) — One decision's receipt and any part not stored yet, or False (a warning) when refused.
- `prefilter_receipt(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 94)
- `prefilter_part(connection: sqlite3.Connection, content_hash: str) -> Any` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 99)
- `insert_objective(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 106) — One decision's frozen objective, or False (a warning) when refused.
- `insert_measurement_event(connection: sqlite3.Connection, *, decision_id: str, state: str, reason: str='', practice_item_id: str | None=None, attempt_id: str | None=None, detail: Mapping[str, Any] | None=None, at: str, episode: str='', non_service_type: str | None=None, delay: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 131) — A measurement's state, once per reason and episode: a repeat is a no-op (returns False).
- `latest_episode(connection: sqlite3.Connection, decision_id: str, *, reason: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 163) — The episode the newest ``due`` or ``offered`` state of this check opened: a loss is counted once per it.
- `due_recorded(connection: sqlite3.Connection, decision_id: str, *, reason: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 172) — Has a settlement written this check's ``due`` (any episode)?
- `reading_exposures_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 180)
- `newest_reading_exposure(connection: sqlite3.Connection) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 184) — The newest source time on record: where the next sweep's window starts.
- `reading_receipts(connection: sqlite3.Connection) -> set[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 190) — ``(LO, source time)`` of every stored reading receipt, data capture's own and AD's where its logging wrote any.
- `sections_read_by_coverage(connection: sqlite3.Connection) -> list[tuple[str, str]]` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 201) — ``(LO, completed_at)`` of every completed section, for each LO its coverage rows name: what a section's LOs come to from coverage alone, read live so a row added after the section was recorded still counts.
- `reading_exposure_recorded(connection: sqlite3.Connection, where: str, args: Iterable[Any]=()) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 213)
- `insert_reading_exposure(connection: sqlite3.Connection, *, kind: str, subkind: str, source_table: str, source_id: str, source_written_at: str, learning_object_id: str, mapping_version: str, swept_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 217) — One reading exposure on one LO, once: a repeat is a no-op (returns False).
- `objectives(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 229) — Every frozen objective by decision id, ``[]`` of absent tables tolerated.
- `measurement_events(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 237)

### Module constants

- `RECEIPT_TABLES` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 22)
- `OBJECTIVE_TABLES` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 23)
- `READING_EXPOSURES` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 25)
- `READING_RECEIPT_TABLES` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 27)
- `RECEIPT_COLUMNS` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 29)
- `OBJECTIVE_COLUMNS` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 35)
- `MEASUREMENT_STATES` ([src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py), line 40)

### Explicit exports

`__all__` declares:

- `READING_EXPOSURES`
- `MEASUREMENT_STATES`
- `OBJECTIVE_COLUMNS`
- `RECEIPT_COLUMNS`
- `insert_measurement_event`
- `insert_reading_exposure`
- `latest_episode`
- `READING_RECEIPT_TABLES`
- `newest_reading_exposure`
- `reading_exposure_recorded`
- `reading_receipts`
- `sections_read_by_coverage`
- `reading_exposures_present`
- `insert_objective`
- `insert_prefilter_receipt`
- `measurement_events`
- `objectives`
- `objectives_present`
- `prefilter_part`
- `prefilter_receipt`
- `receipts_present`

## Internal implementation anchors

- `_present(connection: sqlite3.Connection, tables: Iterable[str]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/data_capture.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; statically calls `due_recorded`, `insert_measurement_event`, `insert_objective`, `latest_episode`, `objectives_present`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `module`; statically calls `insert_prefilter_receipt`, `prefilter_part`, `prefilter_receipt`, `receipts_present`
- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; statically calls `insert_reading_exposure`, `newest_reading_exposure`, `reading_exposure_recorded`, `reading_exposures_present`, `reading_receipts`, `sections_read_by_coverage`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `measurement_events`, `objectives`, `objectives_present`, `receipts_present`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `module`; statically calls `measurement_events`, `objectives`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`, `zlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]], [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]], [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]], [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/data_capture_a2_measurement_helpers.py](../../../../../../../tests/data_capture_a2_measurement_helpers.py) — direct import
- [tests/test_data_capture_a1_prefilter.py](../../../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_a_refused_receipt_never_blocks_the_block`
- [tests/test_data_capture_a4_delayed_completion.py](../../../../../../../tests/test_data_capture_a4_delayed_completion.py) — direct import
- [tests/test_data_capture_codex_rereview.py](../../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f10_the_store_keeps_one_row_per_episode`
- [tests/test_data_capture_codex_review.py](../../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f2_a_warm_answer_consumes_the_check_but_keeps_the_measurement_duty`
- [tests/test_data_capture_landing_review.py](../../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_below_the_receipts_table_the_read_is_activity_alone`
- [tests/test_data_capture_phone.py](../../../../../../../tests/test_data_capture_phone.py) — direct import
- [tests/test_ro0_codex_verify.py](../../../../../../../tests/test_ro0_codex_verify.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/data_capture.py](../../../../../../../src/learnloop/db/stores/data_capture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
