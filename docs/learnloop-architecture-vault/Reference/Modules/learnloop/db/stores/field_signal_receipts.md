---
title: "learnloop.db.stores.field_signal_receipts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/field_signal_receipts.py"
source_paths:
  - "src/learnloop/db/stores/field_signal_receipts.py"
source_commit: "eab475869142f70f0de9bbd3320610108e2ac9bd"
source_commit_timestamp: "2026-10-24T15:07:17-04:00"
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
  - "learnloop.db.stores.field_signal_receipts module"
  - "src/learnloop/db/stores/field_signal_receipts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.field_signal_receipts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.field_signal_receipts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for RW2d's ``field_signal_receipts`` (migration 219).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/field_signal_receipts.py](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py) |
| Source lines | 51 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `eab475869142f70f0de9bbd3320610108e2ac9bd` |
| Commit timestamp | `2026-10-24T15:07:17-04:00` |

## Public API

- `table_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py), line 20)
- `insert_receipt(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py), line 26) — Insert once per ``receipt_key``; True when a new row was written.
- `receipts(connection: sqlite3.Connection, *, learning_object_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py), line 38)

### Module constants

- `_COLUMNS` ([src/learnloop/db/stores/field_signal_receipts.py](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py), line 14)

### Explicit exports

`__all__` declares:

- `insert_receipt`
- `receipts`
- `table_present`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `module`; statically calls `insert_receipt`, `table_present`

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

Static participation evidence comes from [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_rw2d_receipts_migration.py](../../../../../../../tests/test_rw2d_receipts_migration.py) — direct import
  - `test_219_on_the_durability_lane`
  - `test_the_receipts_are_append_only_and_keyed_once`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/field_signal_receipts.py](../../../../../../../src/learnloop/db/stores/field_signal_receipts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
