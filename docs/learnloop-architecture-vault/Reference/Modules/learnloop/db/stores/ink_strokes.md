---
title: "learnloop.db.stores.ink_strokes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/ink_strokes.py"
source_paths:
  - "src/learnloop/db/stores/ink_strokes.py"
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
  - "learnloop.db.stores.ink_strokes module"
  - "src/learnloop/db/stores/ink_strokes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.ink_strokes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.ink_strokes` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL for the learner's ink (migration 267): ``ink_strokes`` (RAW_LEDGER) and ``ink_transcriptions`` (RECEIPT), both append-only by trigger.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/ink_strokes.py](../../../../../../../src/learnloop/db/stores/ink_strokes.py) |
| Source lines | 107 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `insert_save(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 29)
- `save(connection: sqlite3.Connection, ink_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 38)
- `owner_saves(connection: sqlite3.Connection, owner_kind: str, owner_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 43) — Every save and erase of one owner, in write order.
- `owners_with_ink(connection: sqlite3.Connection, owner_kind: str, owner_ids: Iterable[str]) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 52)
- `annotation_exists(connection: sqlite3.Connection, annotation_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 63)
- `extraction_exists(connection: sqlite3.Connection, extraction_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 67)
- `source_extraction_ids(connection: sqlite3.Connection, source_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 71) — Every reading (extraction) of a source's revisions, oldest first.
- `insert_reading(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 80)
- `reading_for(connection: sqlite3.Connection, owner_kind: str, owner_id: str, content_hash: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 88) — The reading of exactly these strokes of this owner, if they were read.
- `latest_reading(connection: sqlite3.Connection, owner_kind: str, owner_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 98) — The owner's newest reading (of whatever strokes stood then).

### Module constants

- `_STROKE_COLUMNS` ([src/learnloop/db/stores/ink_strokes.py](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 14)
- `_READING_COLUMNS` ([src/learnloop/db/stores/ink_strokes.py](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 16)

### Explicit exports

`__all__` declares:

- `annotation_exists`
- `extraction_exists`
- `source_extraction_ids`
- `insert_reading`
- `insert_save`
- `latest_reading`
- `owner_saves`
- `owners_with_ink`
- `reading_for`
- `save`

## Internal implementation anchors

- `_row(row: sqlite3.Row | tuple | None, columns: tuple[str, ...]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/ink_strokes.py), line 20)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; statically calls `annotation_exists`, `extraction_exists`, `insert_save`, `latest_reading`, `owner_saves`, `owners_with_ink`, `save`, `source_extraction_ids`
- [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] — imports `module`; statically calls `annotation_exists`, `insert_reading`, `owner_saves`, `reading_for`

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

Static participation evidence comes from [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]], [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — imports consumer [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]]
- [tests/ink_helpers.py](../../../../../../../tests/ink_helpers.py) — imports consumer [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]]
- [tests/test_reader_rd8a_ink.py](../../../../../../../tests/test_reader_rd8a_ink.py) — imports consumer [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]]
- [tests/test_reader_rd8a_render.py](../../../../../../../tests/test_reader_rd8a_render.py) — imports consumer [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]]
- [tests/test_reader_rd8a_transcribe.py](../../../../../../../tests/test_reader_rd8a_transcribe.py) — imports consumer [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/ink_strokes.py](../../../../../../../src/learnloop/db/stores/ink_strokes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
