---
title: "learnloop.pads.ink"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/ink.py"
source_paths:
  - "src/learnloop/pads/ink.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.pads.ink module"
  - "src/learnloop/pads/ink.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.ink`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.ink` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: The learner's ink (spec §10.10, §15.1): ``ink.save``, the ``erase_ink`` pad op and the reads that return an owner's strokes as they stand.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/ink.py](../../../../../../src/learnloop/pads/ink.py) |
| Source lines | 389 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InkError(LookupError)` ([source](../../../../../../src/learnloop/pads/ink.py), line 41) — An ink request that cannot be served (``code`` names why).
  - `__init__(self, code: str, message: str) -> None` (line 44; internal)
- `class InkStroke(WireModel)` ([source](../../../../../../src/learnloop/pads/ink.py), line 50)
  - `_finite_and_in_range(cls, points: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]` (line 57; internal)
- `class PointerMeta(WireModel)` ([source](../../../../../../src/learnloop/pads/ink.py), line 68) — How the strokes were drawn: the pointer (touch never draws, spec §10.10) and the screen's device pixel ratio (the resolution the learner saw them at, which the server renders them at; unknown, one device pixel per CSS pixel).
- `class InkOwner(WireModel)` ([source](../../../../../../src/learnloop/pads/ink.py), line 77) — One block, one annotation, or one reading of a source (``extraction_id``: ink drawn on the page that became no mark; it is the learner's marks, never read or emitted).
  - `_exactly_one(self) -> 'InkOwner'` (line 86; internal)
  - `kind(self) -> str` (line 92; public)
  - `id(self) -> str` (line 96; public)
  - `of(owner_kind: str, owner_id: str) -> 'InkOwner'` (line 100; public)
- `canonical(value: Any) -> bytes` ([source](../../../../../../src/learnloop/pads/ink.py), line 104)
- `content_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/pads/ink.py), line 108) — The sha256 of ``value``'s canonical JSON: what a save's retry and a reading's reuse compare.
- `encode(value: Any) -> bytes` ([source](../../../../../../src/learnloop/pads/ink.py), line 114)
- `decode(blob: bytes) -> Any` ([source](../../../../../../src/learnloop/pads/ink.py), line 118)
- `standing(saves: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]` ([source](../../../../../../src/learnloop/pads/ink.py), line 126) — An owner's strokes as they stand (each with the ``ink_id`` that saved it) and the finest device pixel ratio they were drawn at.
- `strokes_hash(strokes: list[dict[str, Any]]) -> str` ([source](../../../../../../src/learnloop/pads/ink.py), line 143) — The hash of standing strokes (ids and points, in order): a reading of them is keyed by it.
- `save_ink(repository: Any, *, client_id: str, seq: int, owner: InkOwner, ink_id: str, strokes: list[InkStroke], pointer_meta: PointerMeta, clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink.py), line 181) — ``ink.save``: one batch holding one save, applied once and in order: ``{applied_seq, ink_id, results}``.
- `erase_in_batch(connection: Any, *, pad_id: str, block_id: str, erase_id: str | None, stroke_ids: list[str], client_id: str, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink.py), line 218) — The ``erase_ink`` pad op, inside the pad batch's transaction: a tombstone over standing strokes of one ink block of this pad.
- `copy_to_lifted(connection: Any, *, from_block_id: str, to_block_id: str, client_id: str, now: str) -> None` ([source](../../../../../../src/learnloop/pads/ink.py), line 243) — A lifted ink line's handwriting (``lift_out``, inside the pad batch): the standing strokes of the block it was lifted from, saved again for the lifted block (the same stroke ids and points, so the same hash), and the reading of exactly those strokes kept for it too, so nothing i…
- `erase_ink(repository: Any, *, client_id: str, seq: int, owner: InkOwner, erase_id: str, stroke_ids: list[str], clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink.py), line 281) — ``ink.erase``: one batch erasing strokes of an annotation's or a reading's ink (a block's ink is erased by ``pad.apply``'s ``erase_ink``, in its pad's batch).
- `owner_of(connection: Any, ink_id: str) -> InkOwner` ([source](../../../../../../src/learnloop/pads/ink.py), line 309)
- `reading_decision(connection: Any, row: dict[str, Any]) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/pads/ink.py), line 316) — What a block's reading does to its block, now: ``applied`` (it is the head's words), ``write`` (it becomes them), or ``refused`` with why (the block removed, the learner's words standing, or strokes that changed since they were read: a reading finishing after a newer one never r…
- `owner_view(connection: Any, owner_kind: str, owner_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/ink.py), line 337) — One owner's standing strokes, their hash and its reading (``current`` when it read exactly these strokes).
- `ink_for_pad(repository: Any, pad_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/ink.py), line 358) — The ink of a pad's standing ink blocks, in the pad's block order.
- `ink_for_source(repository: Any, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/ink.py), line 370) — The ink of a source's listed annotations (a deleted annotation's ink is not listed), then the ink on its readings' pages (owner kind ``source``, one owner per reading, never read).

### Module constants

- `ENCODING` ([src/learnloop/pads/ink.py](../../../../../../src/learnloop/pads/ink.py), line 33)
- `PRESSURE_RANGE` ([src/learnloop/pads/ink.py](../../../../../../src/learnloop/pads/ink.py), line 37)
- `TILT_RANGE` ([src/learnloop/pads/ink.py](../../../../../../src/learnloop/pads/ink.py), line 38)

### Explicit exports

`__all__` declares:

- `ANNOTATION`
- `BLOCK`
- `ENCODING`
- `ERASE`
- `SOURCE`
- `erase_ink`
- `InkError`
- `InkOwner`
- `InkStroke`
- `PointerMeta`
- `STROKES`
- `canonical`
- `content_hash`
- `decode`
- `encode`
- `erase_in_batch`
- `ink_for_pad`
- `ink_for_source`
- `owner_of`
- `copy_to_lifted`
- `owner_view`
- `reading_decision`
- `save_ink`
- `standing`
- `strokes_hash`

## Internal implementation anchors

- `_strokes_value(strokes: list[InkStroke]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/ink.py), line 122)
- `_owner_pad(connection: Any, owner: InkOwner) -> str` ([source](../../../../../../src/learnloop/pads/ink.py), line 149) — The pad of a block owner ('' for an annotation), checking the owner can take ink.
- `_receipt_pad(repository: Any, owner: InkOwner) -> str` ([source](../../../../../../src/learnloop/pads/ink.py), line 173)
- `_insert_erase(connection: Any, owner: InkOwner, erase_id: str, stroke_ids: list[str], client_id: str, now: str) -> None` ([source](../../../../../../src/learnloop/pads/ink.py), line 265)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] — imports `module`; statically calls `copy_to_lifted`, `erase_in_batch`
- [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] — imports `module`; statically calls `InkError`, `owner_of`, `reading_decision`, `standing`, `strokes_hash`
- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `module`; statically calls `erase_ink`, `ink_for_pad`, `ink_for_source`, `save_ink`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/ink_strokes|learnloop.db.stores.ink_strokes]] — imports `module`; calls `annotation_exists`, `extraction_exists`, `insert_reading`, `insert_save`, `latest_reading`, `owner_saves`, `owners_with_ink`, `reading_for`, `save`, `source_extraction_ids`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `head`, `heads`, `pad`
- [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] — imports `PAD`
- [[Reference/Modules/learnloop/desks/content_ref|learnloop.desks.content_ref]] — imports `WireModel`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `OpRefused`, `apply_batch`, `run_op`; calls `OpRefused`, `apply_batch`, `run_op`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`, `zlib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]], [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]], [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/ink_helpers.py](../../../../../../tests/ink_helpers.py) — direct import
- [tests/test_reader_rd8a_fix.py](../../../../../../tests/test_reader_rd8a_fix.py) — direct import
  - `test_a_partial_erase_leaves_the_words_until_the_line_is_read_again`
  - `test_lifting_an_ink_line_out_keeps_its_handwriting_and_its_reading`
- [tests/test_reader_rd8a_fix_rpcs.py](../../../../../../tests/test_reader_rd8a_fix_rpcs.py) — direct import
  - `test_the_listed_reading_beside_the_learners_correction_says_why_it_is_not_the_words`
- [tests/test_reader_rd8a_ink.py](../../../../../../tests/test_reader_rd8a_ink.py) — direct import
  - `test_a_malformed_stroke_is_refused`
  - `test_a_margin_notes_ink_is_listed_with_its_source`
  - `test_a_pad_lists_only_its_standing_ink_blocks_with_ink`
  - `test_a_retried_batch_returns_its_receipt_and_a_resent_ink_id_is_a_no_op`
  - `test_a_save_keeps_every_point_as_sent_compressed_with_its_hash`
  - `test_an_owner_is_one_block_one_annotation_or_one_reading`
  - `test_erasing_tombstones_strokes_and_the_standing_ink_and_its_hash_follow`
  - `test_ink_on_a_page_is_erased_by_ink_erase_and_a_retry_is_a_no_op`
  - `test_ink_on_a_page_is_kept_for_its_reading_and_listed_with_its_source`
  - `test_ink_shares_the_clients_one_sequence_with_pad_batches`
  - `test_touch_never_draws_and_an_owner_is_one_thing`
- [tests/test_reader_rd8a_render.py](../../../../../../tests/test_reader_rd8a_render.py) — direct import
- [tests/test_reader_rd8a_transcribe.py](../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import
  - `test_a_margin_notes_reading_is_kept_and_returned_never_written_into_the_note`

## Modification guidance

- Make changes here when the responsibility remains ink within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/ink.py](../../../../../../src/learnloop/pads/ink.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
