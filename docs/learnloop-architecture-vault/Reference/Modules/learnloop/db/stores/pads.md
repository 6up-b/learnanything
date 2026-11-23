---
title: "learnloop.db.stores.pads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/pads.py"
source_paths:
  - "src/learnloop/db/stores/pads.py"
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
  - "learnloop.db.stores.pads module"
  - "src/learnloop/db/stores/pads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.pads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.pads` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for the workbench's scratchpads (migration 262): ``pads`` (WORKFLOW) and the append-only ``pad_block_versions`` and ``pad_block_anchors`` (RAW_LEDGER, enforced by triggers).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py) |
| Source lines | 67 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_pad(connection: sqlite3.Connection, *, pad_id: str, kind: str, title: str, home_desk_id: str | None, workbench_session_id: str | None, lesson_id: str | None, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 19)
- `update_pad(connection: sqlite3.Connection, pad_id: str, fields: Mapping[str, Any], now: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 28) — Set ``fields`` on one pad and count the op in its version; returns the new version.
- `touch_pad(connection: sqlite3.Connection, pad_id: str, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 40) — A block of the pad changed: the pad's last-changed time moves, its metadata version does not.
- `insert_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 46)
- `insert_anchor_event(connection: sqlite3.Connection, *, event_id: str, block_id: str, extraction_id: str, span_id: str, anchor: Mapping[str, Any], annotation_id: str | None, action: str, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 56)

### Module constants

- `_PAD_FIELDS` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 12)
- `VERSION_COLUMNS` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 13)

### Explicit exports

`__all__` declares:

- `VERSION_COLUMNS`
- `insert_anchor_event`
- `insert_pad`
- `insert_version`
- `touch_pad`
- `update_pad`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `module`; statically calls `insert_pad`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `module`; statically calls `insert_anchor_event`, `insert_pad`, `insert_version`, `touch_pad`, `update_pad`

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

Static participation evidence comes from [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/desk_helpers.py](../../../../../../../tests/desk_helpers.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd0_protocol.py](../../../../../../../tests/test_reader_rd0_protocol.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd1_model_parity.py](../../../../../../../tests/test_reader_rd1_model_parity.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd4_emission.py](../../../../../../../tests/test_reader_rd4_emission.py) — imports consumer [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
