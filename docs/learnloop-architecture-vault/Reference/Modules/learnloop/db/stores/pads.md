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
| Source lines | 188 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `pad(connection: sqlite3.Connection, pad_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 40)
- `insert_pad(connection: sqlite3.Connection, *, pad_id: str, kind: str, title: str, home_desk_id: str | None, workbench_session_id: str | None, lesson_id: str | None, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 45)
- `update_pad(connection: sqlite3.Connection, pad_id: str, fields: Mapping[str, Any], now: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 54) — Set ``fields`` on one pad and count the op in its version; returns the new version.
- `touch_pad(connection: sqlite3.Connection, pad_id: str, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 66) — A block of the pad changed: the pad's last-changed time moves, its metadata version does not.
- `running_pad_ids(connection: sqlite3.Connection, desk_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 72)
- `list_pads(connection: sqlite3.Connection, *, desk_id: str | None, kept: bool | None, query: str | None, after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 78) — Pads, most recently changed first; ``query`` matches the title or a standing block's text.
- `head(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 105)
- `heads(connection: sqlite3.Connection, pad_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 110) — Every block head of one pad (tombstones included), ordered by position, then block id.
- `first_versions(connection: sqlite3.Connection, block_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 117)
- `version_exists(connection: sqlite3.Connection, version_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 127)
- `insert_version(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 131)
- `insert_anchor_event(connection: sqlite3.Connection, *, event_id: str, block_id: str, extraction_id: str, span_id: str, anchor: Mapping[str, Any], annotation_id: str | None, action: str, now: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 144)
- `standing_anchors_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 162) — The links that stand (the latest event per block and passage is a link), in written order.
- `standing_anchors_for_spans(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 173) — Every standing link onto the given readings, each with its block's head (pad and kind).

### Module constants

- `_PAD_FIELDS` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 13)
- `VERSION_COLUMNS` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 14)
- `_HEADS` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 18)
- `_STANDING` ([src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py), line 155)

### Explicit exports

`__all__` declares:

- `VERSION_COLUMNS`
- `first_versions`
- `head`
- `heads`
- `insert_anchor_event`
- `insert_pad`
- `insert_version`
- `list_pads`
- `pad`
- `running_pad_ids`
- `standing_anchors_for_blocks`
- `standing_anchors_for_spans`
- `touch_pad`
- `update_pad`
- `version_exists`

## Internal implementation anchors

- `_rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 24)
- `_decoded(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/pads.py), line 30)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `module`; statically calls `running_pad_ids`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `module`; statically calls `first_versions`, `head`, `heads`, `insert_anchor_event`, `insert_pad`, `insert_version`, `list_pads`, `pad`, `standing_anchors_for_blocks`, `touch_pad`, `update_pad`, `version_exists`
- [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] — imports `module`; statically calls `head`, `standing_anchors_for_spans`

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

Static participation evidence comes from [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/desk_helpers.py](../../../../../../../tests/desk_helpers.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd0_protocol.py](../../../../../../../tests/test_reader_rd0_protocol.py) — imports consumer [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]]
- [tests/test_reader_rd0_reads.py](../../../../../../../tests/test_reader_rd0_reads.py) — imports consumer [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/pads.py](../../../../../../../src/learnloop/db/stores/pads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
