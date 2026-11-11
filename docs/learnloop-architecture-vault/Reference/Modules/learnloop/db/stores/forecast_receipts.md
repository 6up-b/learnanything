---
title: "learnloop.db.stores.forecast_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/forecast_receipts.py"
source_paths:
  - "src/learnloop/db/stores/forecast_receipts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.db.stores.forecast_receipts module"
  - "src/learnloop/db/stores/forecast_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.forecast_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.forecast_receipts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Saved forecasts: ``forecast_receipts`` persistence (append-only, migration 206).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/forecast_receipts.py](../../../../../../../src/learnloop/db/stores/forecast_receipts.py) |
| Source lines | 126 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `has_table(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 38)
- `insert_receipt(connection: sqlite3.Connection, *, receipt_key: str, kind: str, forecaster: str, forecaster_version: str, scope: str, decision_kind: str, binding_kind: str, event: str, forecast: Mapping[str, Any], inputs: Mapping[str, Any], inputs_hash: str, inputs_as_of: str, parameters: Any, versions: Mapping[str, Any], created_at: str, status: str='ok', **columns: Any) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 44) — Append one receipt; None when its receipt key already exists.
- `list_receipts(connection: sqlite3.Connection, *, since: str | None=None, kind: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 101) — Every receipt (decoded), oldest first; ``[]`` on a database without the table.

### Module constants

- `TABLE` ([src/learnloop/db/stores/forecast_receipts.py](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 19)
- `COLUMNS` ([src/learnloop/db/stores/forecast_receipts.py](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 21)
- `OPTIONAL_COLUMNS` ([src/learnloop/db/stores/forecast_receipts.py](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 31)

### Explicit exports

`__all__` declares:

- `COLUMNS`
- `OPTIONAL_COLUMNS`
- `TABLE`
- `has_table`
- `insert_receipt`
- `list_receipts`

## Internal implementation anchors

- `_decode(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/forecast_receipts.py), line 92)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `module`; statically calls `list_receipts`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `module`; statically calls `has_table`, `list_receipts`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `module`; statically calls `has_table`, `insert_receipt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] — imports `_dumps`, `_loads`; calls `_dumps`, `_loads`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/forecast_receipts_helpers.py](../../../../../../../tests/forecast_receipts_helpers.py) — direct import
- [tests/test_cold_retry_reschedule.py](../../../../../../../tests/test_cold_retry_reschedule.py) — direct import
- [tests/test_forecast_receipts.py](../../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_failed_receipt_never_breaks_its_diagnosis`
- [tests/test_forecast_receipts_landing.py](../../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_a_failed_forecast_receipt_keeps_the_diagnosis_and_its_provenance_record`
- [tests/test_teacher_te2log_node_held.py](../../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_a_refused_forecast_rolls_back_alone_and_the_plan_stands`
  - `test_one_refused_node_forecast_leaves_its_siblings`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/forecast_receipts.py](../../../../../../../src/learnloop/db/stores/forecast_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
