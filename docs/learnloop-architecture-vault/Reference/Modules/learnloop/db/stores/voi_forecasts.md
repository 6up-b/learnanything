---
title: "learnloop.db.stores.voi_forecasts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/voi_forecasts.py"
source_paths:
  - "src/learnloop/db/stores/voi_forecasts.py"
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
  - "learnloop.db.stores.voi_forecasts module"
  - "src/learnloop/db/stores/voi_forecasts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.voi_forecasts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.voi_forecasts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: EVSI calibration Part B persistence: ``voi_forecasts`` receipts (append-only).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/voi_forecasts.py](../../../../../../../src/learnloop/db/stores/voi_forecasts.py) |
| Source lines | 111 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `has_table(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 42)
- `insert_forecast(connection: sqlite3.Connection, *, receipt_key: str, site: str, verdict: str, forecast: Mapping[str, Any], parameters: Any, versions: Mapping[str, Any], forecast_version: str, candidate_count: int, decision_ref: str | None=None, learning_object_id: str | None=None, probe_episode_id: str | None=None, presentation_id: str | None=None, source_attempt_id: str | None=None, factor_id: str | None=None, chosen_ref: str | None=None, chosen_practice_item_id: str | None=None, scheduler_candidate_id: str | None=None, eig_nats: float | None=None, evsi_point_minutes: float | None=None, evsi_lcb_minutes: float | None=None, p_action_change: float | None=None, algorithm_version: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 48) — Append one forecast; None when its receipt key already exists.
- `list_forecasts(connection: sqlite3.Connection, *, since: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 102)

### Module constants

- `TABLE` ([src/learnloop/db/stores/voi_forecasts.py](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 17)
- `_COLUMNS` ([src/learnloop/db/stores/voi_forecasts.py](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 19)

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 29)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 33)
- `_decode(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/voi_forecasts.py), line 94)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `_dumps`, `_loads`; statically calls `_dumps`, `_loads`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `module`; statically calls `has_table`, `list_forecasts`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `module`; statically calls `list_forecasts`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; statically calls `has_table`, `insert_forecast`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]], [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_router_composition.py](../../../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_voi_merge_composition.py](../../../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/voi_forecasts_helpers.py](../../../../../../../tests/voi_forecasts_helpers.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/voi_forecasts.py](../../../../../../../src/learnloop/db/stores/voi_forecasts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
