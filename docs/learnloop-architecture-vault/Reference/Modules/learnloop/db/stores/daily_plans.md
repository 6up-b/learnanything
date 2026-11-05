---
title: "learnloop.db.stores.daily_plans"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/daily_plans.py"
source_paths:
  - "src/learnloop/db/stores/daily_plans.py"
source_commit: "7271dbc726eb6e48dfea094c1d704c879b78b5ca"
source_commit_timestamp: "2026-10-13T22:44:21-04:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.daily_plans module"
  - "src/learnloop/db/stores/daily_plans.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.daily_plans`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.daily_plans` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for daily-loop DL1 plan rows (migration 180; built as 174).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/daily_plans.py](../../../../../../../src/learnloop/db/stores/daily_plans.py) |
| Source lines | 355 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7271dbc726eb6e48dfea094c1d704c879b78b5ca` |
| Commit timestamp | `2026-10-13T22:44:21-04:00` |

## Public API

- `insert_plan(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 50)
- `update_plan(connection: sqlite3.Connection, plan_id: str, **fields: Any) -> None` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 62)
- `abandon_open_plans_before(connection: sqlite3.Connection, local_date: str, *, now: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 78) — An open plan from an earlier day is abandoned (§6.10): progress is kept elsewhere.
- `insert_plan_block(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 92)
- `append_block_event(connection: sqlite3.Connection, *, event_id: str, block_id: str, kind: str, detail: Mapping[str, Any] | None, created_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 113)
- `plan_by_id(connection: sqlite3.Connection, plan_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 145)
- `plans_for_date(connection: sqlite3.Connection, local_date: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 150)
- `latest_plan(connection: sqlite3.Connection) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 157)
- `all_plans(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 164)
- `plan_blocks(connection: sqlite3.Connection, plan_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 169)
- `block_events_for(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 188)
- `daily_plan_tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 206)
- `open_learner_state_hypotheses(connection: sqlite3.Connection, learning_object_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 219) — The unresolved causal hypotheses: THE resolution predicate (owner decision 2026-10-12).
- `open_diagnosed_problem_learning_object_ids(connection: sqlite3.Connection) -> frozenset[str]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 275) — LOs with an open diagnosed problem: what "repair" means (owner decision 2026-10-12).
- `plan_served_origins(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 303) — Every plan ``item_served`` receipt, by practice item, oldest first.

### Module constants

- `_PLAN_COLUMNS` ([src/learnloop/db/stores/daily_plans.py](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 28)
- `_PLAN_UPDATABLE` ([src/learnloop/db/stores/daily_plans.py](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 34)
- `OPEN_HYPOTHESIS_STATUSES` ([src/learnloop/db/stores/daily_plans.py](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 216)

### Explicit exports

`__all__` declares:

- `abandon_open_plans_before`
- `all_plans`
- `append_block_event`
- `block_events_for`
- `daily_plan_tables_present`
- `OPEN_HYPOTHESIS_STATUSES`
- `open_learner_state_hypotheses`
- `insert_plan`
- `insert_plan_block`
- `latest_plan`
- `open_diagnosed_problem_learning_object_ids`
- `plan_blocks`
- `plan_by_id`
- `plan_served_origins`
- `plans_for_date`
- `update_plan`

## Internal implementation anchors

- `_json(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 42)
- `_loads(value: str | None) -> Any` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 46)
- `_plan_dict(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/daily_plans.py), line 138)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `abandon_open_plans_before`, `all_plans`, `append_block_event`, `block_events_for`, `daily_plan_tables_present`, `insert_plan`, `insert_plan_block`, `latest_plan`, `open_diagnosed_problem_learning_object_ids`, `plan_blocks`, `plan_by_id`, `plans_for_date`, `update_plan`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; statically calls `plans_for_date`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `open_learner_state_hypotheses`; statically calls `open_learner_state_hypotheses`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `plan_served_origins`; statically calls `plan_served_origins`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `block_events_for`, `daily_plan_tables_present`, `plan_blocks`, `plans_for_date`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `open_learner_state_hypotheses`; statically calls `open_learner_state_hypotheses`
- [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] — imports `module`; statically calls `append_block_event`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `daily_plan_tables_present`, `latest_plan`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_verify_fixes.py](../../../../../../../tests/test_followups_batch6_verify_fixes.py) — direct import
- [tests/test_router_card.py](../../../../../../../tests/test_router_card.py) — direct import
  - `test_a_resolved_promoted_misconception_is_not_an_open_problem`
- [tests/test_voi_merge_composition.py](../../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_the_report_scores_a_project_probe_through_r1s_plan_block`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/daily_plans.py](../../../../../../../src/learnloop/db/stores/daily_plans.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
