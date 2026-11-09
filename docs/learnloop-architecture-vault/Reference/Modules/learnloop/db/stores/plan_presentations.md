---
title: "learnloop.db.stores.plan_presentations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/plan_presentations.py"
source_paths:
  - "src/learnloop/db/stores/plan_presentations.py"
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
  - "learnloop.db.stores.plan_presentations module"
  - "src/learnloop/db/stores/plan_presentations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.plan_presentations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.plan_presentations` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for router R2a's ``plan_presentations`` (migration 202).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/plan_presentations.py](../../../../../../../src/learnloop/db/stores/plan_presentations.py) |
| Source lines | 145 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `plan_presentations_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 23) — Whether the database has the table (a vault below migration 202 has not).
- `presentation_for(connection: sqlite3.Connection, block_id: str, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 31)
- `insert_plan_presentation(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 39) — Append one presentation, or return the standing one for its block and item.
- `presentation_by_id(connection: sqlite3.Connection, presentation_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 64)
- `bindable_presentation(connection: sqlite3.Connection, presentation_id: str | None, *, practice_item_id: str, attempt_id: str | None=None) -> tuple[str | None, str | None]` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 69) — ``(presentation id, None)`` when an attempt on ``practice_item_id`` may bind to it, else ``(None, why)``: unknown, another item's, or already answered by another attempt (``attempt_id``'s own row, a retried write, does not count).
- `presentations_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 100) — Each block's presentations in serving order (``served_at``, then id).
- `presentations_for_controller_decision(connection: sqlite3.Connection, controller_decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 120) — Presentations of every block whose router decision named the staged controller decision, in serving order (plan §5.3).

### Module constants

- `PRESENTATION_COLUMNS` ([src/learnloop/db/stores/plan_presentations.py](../../../../../../../src/learnloop/db/stores/plan_presentations.py), line 17)

### Explicit exports

`__all__` declares:

- `PRESENTATION_COLUMNS`
- `bindable_presentation`
- `insert_plan_presentation`
- `plan_presentations_present`
- `presentation_by_id`
- `presentation_for`
- `presentations_for_blocks`
- `presentations_for_controller_decision`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `bindable_presentation`, `insert_plan_presentation`, `plan_presentations_present`, `presentation_by_id`, `presentation_for`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `bindable_presentation`; statically calls `bindable_presentation`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `bindable_presentation`; statically calls `bindable_presentation`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `presentations_for_blocks`; statically calls `presentations_for_blocks`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `fill_receipt`, `split_receipt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]], [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v2_rereview_fixes.py](../../../../../../../tests/test_mobile_v2_rereview_fixes.py) — direct import
- [tests/test_reader_rw4b_fix6.py](../../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
- [tests/test_ro0_codex_verify.py](../../../../../../../tests/test_ro0_codex_verify.py) — direct import
- [tests/test_ro0_row3_ask_availability.py](../../../../../../../tests/test_ro0_row3_ask_availability.py) — direct import
  - `test_the_reopen_returns_the_first_row`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/plan_presentations.py](../../../../../../../src/learnloop/db/stores/plan_presentations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
