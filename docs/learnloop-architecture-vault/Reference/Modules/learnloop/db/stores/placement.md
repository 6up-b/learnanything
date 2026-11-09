---
title: "learnloop.db.stores.placement"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/placement.py"
source_paths:
  - "src/learnloop/db/stores/placement.py"
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
  - "learnloop.db.stores.placement module"
  - "src/learnloop/db/stores/placement.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.placement`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.placement` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for learner-field F2 placement tables (migrations 172-173).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/placement.py](../../../../../../../src/learnloop/db/stores/placement.py) |
| Source lines | 101 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_assumption_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 27)
- `insert_assumption_return(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 35)
- `insert_quick_check(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 43)
- `finish_quick_check(connection: sqlite3.Connection, calibration_session_id: str, *, finished_at: str, outcome_json: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 57) — Record the split once.
- `insert_quick_check_item(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 71) — Persist one presentation of the quick check (at most k per check).
- `bind_quick_check_item(connection: sqlite3.Connection, calibration_session_id: str, ordinal: int, *, attempt_id: str, answered_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/placement.py), line 85) — Associate a submission with its presentation, once.

### Module constants

- `_DECISION_COLUMNS` ([src/learnloop/db/stores/placement.py](../../../../../../../src/learnloop/db/stores/placement.py), line 15)
- `_RETURN_COLUMNS` ([src/learnloop/db/stores/placement.py](../../../../../../../src/learnloop/db/stores/placement.py), line 21)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `insert_quick_check`, `insert_quick_check_item`; statically calls `insert_quick_check`, `insert_quick_check_item`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `bind_quick_check_item`, `finish_quick_check`, `insert_assumption_decision`, `insert_assumption_return`; statically calls `bind_quick_check_item`, `finish_quick_check`, `insert_assumption_decision`, `insert_assumption_return`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]], [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reading_paths.py](../../../../../../../tests/test_reading_paths.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/placement.py](../../../../../../../src/learnloop/db/stores/placement.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
