---
title: "learnloop.db.stores.workspace_batches"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/workspace_batches.py"
source_paths:
  - "src/learnloop/db/stores/workspace_batches.py"
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
  - "learnloop.db.stores.workspace_batches module"
  - "src/learnloop/db/stores/workspace_batches.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.workspace_batches`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.workspace_batches` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The stored replies of the workbench's write batches (migration 262): ``desk_op_receipts`` and ``pad_op_receipts``, both RECEIPT, append-only by trigger.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/workspace_batches.py](../../../../../../../src/learnloop/db/stores/workspace_batches.py) |
| Source lines | 75 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class StoredReceipt` ([source](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 20)
- `last_seq(connection: sqlite3.Connection, client_id: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 26) — The client's highest applied batch number across both channels (0: none yet).
- `find_receipt(connection: sqlite3.Connection, client_id: str, seq: int) -> StoredReceipt | None` ([source](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 37)
- `insert_receipt(connection: sqlite3.Connection, *, channel: str, client_id: str, seq: int, request_hash: str, result: dict[str, Any], applied_at: str, pad_id: str | None=None) -> None` ([source](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 47)
- `client_heads(connection: sqlite3.Connection) -> list[tuple[str, int]]` ([source](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 65) — Every client's highest applied batch number, by client id.

### Module constants

- `DESK` ([src/learnloop/db/stores/workspace_batches.py](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 15)
- `PAD` ([src/learnloop/db/stores/workspace_batches.py](../../../../../../../src/learnloop/db/stores/workspace_batches.py), line 16)

### Explicit exports

`__all__` declares:

- `DESK`
- `PAD`
- `StoredReceipt`
- `client_heads`
- `find_receipt`
- `insert_receipt`
- `last_seq`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `module`; statically calls `client_heads`, `find_receipt`, `insert_receipt`, `last_seq`
- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `DESK`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `PAD`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]], [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_reader_rd0_protocol.py](../../../../../../../tests/test_reader_rd0_protocol.py) — imports consumer [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]]
- [tests/desk_helpers.py](../../../../../../../tests/desk_helpers.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/workspace_batches.py](../../../../../../../src/learnloop/db/stores/workspace_batches.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
