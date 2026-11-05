---
title: "learnloop.db.stores.router_objective"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/router_objective.py"
source_paths:
  - "src/learnloop/db/stores/router_objective.py"
source_commit: "2ffac8021ab164e5294b86f628c3747099919ac0"
source_commit_timestamp: "2026-11-04T18:38:52-05:00"
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
  - "learnloop.db.stores.router_objective module"
  - "src/learnloop/db/stores/router_objective.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.router_objective`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.router_objective` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: RO0's append-only records (migration 243; spec_router_objective_v1 §4).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py) |
| Source lines | 192 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2ffac8021ab164e5294b86f628c3747099919ac0` |
| Commit timestamp | `2026-11-04T18:38:52-05:00` |

## Public API

- `table_present(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 41)
- `column_present(connection: sqlite3.Connection, table: str, column: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 47) — Whether the database has the column (a vault below migration 243 has not).
- `split_receipt(table: str, row: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 94) — ``row`` as its predecessor wrote it (RO0's fields out), and RO0's fields on it that hold a value.
- `fill_receipt(connection: sqlite3.Connection, table: str, key: Any, values: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 102) — RO0's fields on a row just inserted without them, in their own savepoint, or False: nothing to write (a vault below migration 243 has no such column), or refused, with a warning, and the row stands with them null.
- `insert_session_receipt(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 127) — One session receipt, or False: refused (a warning), or that session already has one of this kind.
- `session_receipt(connection: sqlite3.Connection, session_id: str, kind: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 133)
- `insert_decision_state(connection: sqlite3.Connection, row: Mapping[str, Any], content: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 141) — One decision's state, compressed, or False (a warning) when refused.
- `decision_state(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 150) — One decision's receipt with its state decompressed (read-only), or None.
- `insert_goal_event(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 161)
- `latest_goal_events(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 165) — Each goal's newest lifecycle row, what the next load compares its YAML against.

### Module constants

- `SESSION_RECEIPTS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 21)
- `DECISION_STATE` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 22)
- `GOAL_EVENTS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 23)
- `SESSION_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 25)
- `STATE_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 30)
- `GOAL_COLUMNS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 35)
- `RECEIPT_FIELDS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 73)
- `_RECEIPT_KEYS` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 81)
- `_RECEIPT_WHAT` ([src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py), line 85)

### Explicit exports

`__all__` declares:

- `DECISION_STATE`
- `GOAL_COLUMNS`
- `GOAL_EVENTS`
- `SESSION_COLUMNS`
- `SESSION_RECEIPTS`
- `STATE_COLUMNS`
- `column_present`
- `decision_state`
- `insert_decision_state`
- `insert_goal_event`
- `insert_session_receipt`
- `latest_goal_events`
- `RECEIPT_FIELDS`
- `fill_receipt`
- `session_receipt`
- `split_receipt`
- `table_present`

## Internal implementation anchors

- `_append(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_objective.py), line 53)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `module`; statically calls `append`, `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; statically calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] — imports `module`; statically calls `fill_receipt`, `split_receipt`
- [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] — imports `module`; statically calls `column_present`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `module`; statically calls `insert_decision_state`, `table_present`
- [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] — imports `module`; statically calls `column_present`
- [[Reference/Modules/learnloop/router_objective/goal_lifecycle|learnloop.router_objective.goal_lifecycle]] — imports `module`; statically calls `insert_goal_event`, `latest_goal_events`, `table_present`
- [[Reference/Modules/learnloop/router_objective/question_state|learnloop.router_objective.question_state]] — imports `module`; statically calls `column_present`, `table_present`
- [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]] — imports `module`; statically calls `table_present`
- [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] — imports `module`; statically calls `insert_session_receipt`, `table_present`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`, `zlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]], [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]], [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]], [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_codex_review.py](../../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_rows7_8_sessions.py](../../../../../../../tests/test_ro0_rows7_8_sessions.py) — direct import
  - `test_a_refused_receipt_rolls_back_alone_and_the_session_stands`
  - `test_the_store_rolls_back_a_refused_row_alone`
- [tests/test_ro0_rows9_13_decision_state.py](../../../../../../../tests/test_ro0_rows9_13_decision_state.py) — direct import
  - `test_a_refused_state_rolls_back_alone_and_the_decision_stands`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/router_objective.py](../../../../../../../src/learnloop/db/stores/router_objective.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
