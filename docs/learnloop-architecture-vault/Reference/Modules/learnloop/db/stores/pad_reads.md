---
title: "learnloop.db.stores.pad_reads"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/pad_reads.py"
source_paths:
  - "src/learnloop/db/stores/pad_reads.py"
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
  - "learnloop.db.stores.pad_reads module"
  - "src/learnloop/db/stores/pad_reads.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.pad_reads`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.pad_reads` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Reads of the workbench's scratchpads (migration 262): ``pads``, ``pad_block_versions`` and ``pad_block_anchors``.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/pad_reads.py](../../../../../../../src/learnloop/db/stores/pad_reads.py) |
| Source lines | 305 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `pad(connection: sqlite3.Connection, pad_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 33)
- `running_pad_ids(connection: sqlite3.Connection, desk_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 38)
- `list_pads(connection: sqlite3.Connection, *, desk_id: str | None, kept: bool | None, query: str | None, after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 43) — Pads, most recently changed first; ``query`` matches the title or a standing block's text.
- `lesson_additions_pads(connection: sqlite3.Connection, lesson_ids: Iterable[str]) -> dict[str, list[str]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 67) — Each lesson's additions pads (spec §11.1, "your additions"), oldest first: the first is where new notes go (a second is refused since); pads two windows made before that rule are all kept and all named.
- `head(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 83)
- `heads(connection: sqlite3.Connection, pad_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 88) — Every block head of one pad (tombstones included), ordered by position, then block id.
- `first_versions(connection: sqlite3.Connection, block_ids: Iterable[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 95)
- `chain(connection: sqlite3.Connection, block_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 105) — One block's versions, oldest first, by following its supersession links from its first version.
- `version(connection: sqlite3.Connection, version_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 119)
- `lift_stub_for(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 124) — The stub version a lift-out left in the block a lifted block came from, or None.
- `block_ids(connection: sqlite3.Connection) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 132) — Every block with a version, in a stable order.
- `version_exists(connection: sqlite3.Connection, version_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 138)
- `standing_anchors_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 149) — The links that stand (the latest event per block and passage is a link), in written order.
- `standing_anchors_for_spans(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 160) — Every standing link onto the given readings, each with its block's head (pad and kind).
- `latest_anchor_event(connection: sqlite3.Connection, block_id: str, extraction_id: str, span_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 171) — The newest link or unlink event between one block and one passage (the anchor's head), or None.
- `anchor_event_exists(connection: sqlite3.Connection, event_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 180)
- `submission(connection: sqlite3.Connection, submission_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 192)
- `submissions_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 197)
- `carried(connection: sqlite3.Connection, carried_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 213)
- `list_carried(connection: sqlite3.Connection, *, states: Iterable[str], desk_id: str | None, after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 218) — Carried questions in the given states, longest carried first (then by id).
- `carried_on_readings(connection: sqlite3.Connection, extraction_ids: Iterable[str], states: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 234) — Carried questions in the given states whose anchor is on one of the readings.
- `carried_event_exists(connection: sqlite3.Connection, event_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 249)
- `carried_events(connection: sqlite3.Connection, carried_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 254)
- `proposal(connection: sqlite3.Connection, proposal_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 265)
- `proposal_for_version(connection: sqlite3.Connection, version_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 270)
- `proposals_for_versions(connection: sqlite3.Connection, version_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 275)
- `label(connection: sqlite3.Connection, label_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 285)
- `labels_for(connection: sqlite3.Connection, proposal_kind: str, proposal_ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 290)

### Module constants

- `_HEADS` ([src/learnloop/db/stores/pad_reads.py](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 14)
- `_STANDING` ([src/learnloop/db/stores/pad_reads.py](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 142)

### Explicit exports

`__all__` declares:

- `anchor_event_exists`
- `block_ids`
- `carried`
- `carried_event_exists`
- `carried_events`
- `carried_on_readings`
- `chain`
- `first_versions`
- `head`
- `heads`
- `label`
- `labels_for`
- `latest_anchor_event`
- `lift_stub_for`
- `list_carried`
- `list_pads`
- `pad`
- `proposal`
- `proposal_for_version`
- `proposals_for_versions`
- `running_pad_ids`
- `standing_anchors_for_blocks`
- `standing_anchors_for_spans`
- `submission`
- `submissions_for_blocks`
- `version`
- `version_exists`

## Internal implementation anchors

- `_rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 20)
- `_decoded(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 26)
- `_table(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 187)
- `_carried_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 206)
- `_proposal_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/pad_reads.py), line 259)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]] — imports `module`; statically calls `head`
- [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]] — imports `module`; statically calls `pad`, `running_pad_ids`
- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `module`; statically calls `anchor_event_exists`, `first_versions`, `head`, `heads`, `latest_anchor_event`, `lesson_additions_pads`, `list_pads`, `pad`, `standing_anchors_for_blocks`, `version`, `version_exists`
- [[Reference/Modules/learnloop/pads/carried|learnloop.pads.carried]] — imports `module`; statically calls `carried`, `carried_event_exists`, `carried_events`, `list_carried`
- [[Reference/Modules/learnloop/pads/cells|learnloop.pads.cells]] — imports `module`; statically calls `heads`, `pad`
- [[Reference/Modules/learnloop/pads/drain|learnloop.pads.drain]] — imports `module`; statically calls `heads`, `list_pads`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `module`; statically calls `block_ids`, `chain`, `head`, `heads`, `lift_stub_for`, `pad`, `standing_anchors_for_blocks`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; statically calls `head`, `heads`, `pad`
- [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] — imports `module`; statically calls `head`
- [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] — imports `module`; statically calls `head`, `heads`, `label`, `labels_for`, `pad`, `proposal`, `proposal_for_version`, `proposals_for_versions`
- [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] — imports `module`; statically calls `head`, `pad`, `submission`, `submissions_for_blocks`, `version`
- [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] — imports `module`; statically calls `carried_on_readings`, `head`, `standing_anchors_for_spans`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `lesson_additions_pads`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `module`; statically calls `head`, `labels_for`
- [[Reference/Modules/learnloop_sidecar/workbench_protection|learnloop_sidecar.workbench_protection]] — imports `module`; statically calls `head`, `standing_anchors_for_blocks`

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

Static participation evidence comes from [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]], [[Reference/Modules/learnloop/desks/workspace|learnloop.desks.workspace]], [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/pads/carried|learnloop.pads.carried]], [[Reference/Modules/learnloop/pads/cells|learnloop.pads.cells]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notebook_pad_cells.py](../../../../../../../tests/test_notebook_pad_cells.py) — direct import
  - `test_a_cells_code_is_never_learner_text`
  - `test_cells_are_pad_blocks_with_append_only_versions_and_their_provenance`
- [tests/test_reader_ink_glm_ocr.py](../../../../../../../tests/test_reader_ink_glm_ocr.py) — direct import
  - `test_the_reading_is_the_text_glm_ocr_recognised_unchanged`
- [tests/test_reader_rd8a_fix.py](../../../../../../../tests/test_reader_rd8a_fix.py) — direct import
- [tests/test_reader_rd8a_transcribe.py](../../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/pad_reads.py](../../../../../../../src/learnloop/db/stores/pad_reads.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
