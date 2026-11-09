---
title: "learnloop.db.stores.followup_value"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/followup_value.py"
source_paths:
  - "src/learnloop/db/stores/followup_value.py"
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
  - "learnloop.db.stores.followup_value module"
  - "src/learnloop/db/stores/followup_value.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.followup_value`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.followup_value` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for ``followup_value_decisions`` (migration 201).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/followup_value.py](../../../../../../../src/learnloop/db/stores/followup_value.py) |
| Source lines | 71 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `table_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/followup_value.py), line 25)
- `insert_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/followup_value.py), line 31) — Append one decision; its ordinal is the attempt's next (one statement, so it is atomic under SQLite's write lock).
- `decisions_for_attempt(connection: sqlite3.Connection, source_attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/followup_value.py), line 59) — Every decision on ``source_attempt_id``, in decision order.

### Module constants

- `COLUMNS` ([src/learnloop/db/stores/followup_value.py](../../../../../../../src/learnloop/db/stores/followup_value.py), line 18)

### Explicit exports

`__all__` declares:

- `COLUMNS`
- `decisions_for_attempt`
- `insert_decision`
- `table_present`

## Internal implementation anchors

- `_decode(row: sqlite3.Row) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/followup_value.py), line 51)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `decisions_for_attempt`, `insert_decision`; statically calls `decisions_for_attempt`, `insert_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_data_capture_a1_prefilter.py](../../../../../../../tests/test_data_capture_a1_prefilter.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/test_data_capture_codex_review.py](../../../../../../../tests/test_data_capture_codex_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/test_mvp021_upgrade.py](../../../../../../../tests/test_mvp021_upgrade.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/test_voi_merge_composition.py](../../../../../../../tests/test_voi_merge_composition.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/test_voi_stopping.py](../../../../../../../tests/test_voi_stopping.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/test_voi_v2.py](../../../../../../../tests/test_voi_v2.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]
- [tests/voi_restore_scenarios.py](../../../../../../../tests/voi_restore_scenarios.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/followup_value.py](../../../../../../../src/learnloop/db/stores/followup_value.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
