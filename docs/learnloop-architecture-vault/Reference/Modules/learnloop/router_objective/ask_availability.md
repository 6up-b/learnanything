---
title: "learnloop.router_objective.ask_availability"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/ask_availability.py"
source_paths:
  - "src/learnloop/router_objective/ask_availability.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.ask_availability module"
  - "src/learnloop/router_objective/ask_availability.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.ask_availability`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.ask_availability` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 row 3: whether Ask was available, per plan presentation and Reader visit.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/ask_availability.py](../../../../../../src/learnloop/router_objective/ask_availability.py) |
| Source lines | 88 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `at_serve(vault: Any, practice_item_id: str) -> int | None` ([source](../../../../../../src/learnloop/router_objective/ask_availability.py), line 26) — 1 or 0 by the server's rule at the serve; None for an item this vault cannot read.
- `serve_fields(vault: Any, connection: Any, practice_item_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/ask_availability.py), line 35) — The presentation row's new column, on or off, at or below migration 243.
- `record_change(vault: Any, repository: Any, *, session_id: str | None, practice_item_id: str, available: bool, reason: str | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/router_objective/ask_availability.py), line 59) — The screen reports Ask's availability on an item it is showing.

### Module constants

- `EVENT_KIND` ([src/learnloop/router_objective/ask_availability.py](../../../../../../src/learnloop/router_objective/ask_availability.py), line 21)
- `_REFUSED_MODES` ([src/learnloop/router_objective/ask_availability.py](../../../../../../src/learnloop/router_objective/ask_availability.py), line 23)

### Explicit exports

`__all__` declares:

- `EVENT_KIND`
- `at_serve`
- `record_change`
- `serve_fields`

## Internal implementation anchors

- `_standing(connection: Any, presentation: dict[str, Any]) -> int | None` ([source](../../../../../../src/learnloop/router_objective/ask_availability.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `serve_fields`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `module`; statically calls `record_change`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `append_block_event`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_report.py](../../../../../../tests/test_ro0_report.py) — direct import
  - `test_each_row_reports_what_was_written_and_measured_bytes`
- [tests/test_ro0_row3_ask_availability.py](../../../../../../tests/test_ro0_row3_ask_availability.py) — direct import
  - `test_a_later_change_is_an_event_and_the_row_stands`
  - `test_an_item_the_plan_did_not_serve_has_no_presentation_to_speak_of`
  - `test_off_nothing_is_written`
  - `test_the_rule_refuses_a_teach_back_and_says_nothing_of_an_unknown_item`

## Modification guidance

- Make changes here when the responsibility remains ask availability within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/ask_availability.py](../../../../../../src/learnloop/router_objective/ask_availability.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
