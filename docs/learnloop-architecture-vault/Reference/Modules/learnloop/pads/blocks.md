---
title: "learnloop.pads.blocks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/pads/blocks.py"
source_paths:
  - "src/learnloop/pads/blocks.py"
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
  - "learnloop.pads.blocks module"
  - "src/learnloop/pads/blocks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-pads"
---

# `learnloop.pads.blocks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.pads.blocks` exists within [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] to own the behavior summarized by its module contract: Scratchpads and their blocks (spec §10, §3.4): ``pad.get``, ``pad.list`` and the ``pad.apply`` ops.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py) |
| Source lines | 566 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CreatePad(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 44)
- `class SetTitle(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 53)
- `class Keep(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 59)
- `class Unkeep(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 64)
- `class InsertBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 69)
- `class KeepBoth(WireModel)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 81) — Where a stale edit's words go instead of being lost (spec §3.5): a new block, client-minted, right after the block's current head, marked with what it conflicted with.
- `class EditBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 91)
- `class RemoveBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 103)
- `class MoveBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 110)
- `class LiftOut(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 118)
- `class LinkAnchor(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 130)
- `class UnlinkAnchor(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 143)
- `class EraseInk(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 152) — The pen's barrel button over an ink block's strokes: a tombstone over their ids (``pads.ink``).
- `class PadNotFound(LookupError)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 195)
- `pad_view(repository: Any, pad_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 242) — ``pad.get``: the pad, its standing blocks in order (removed blocks left out) and their links.
- `pad_list(repository: Any, *, desk_id: str | None=None, query: str | None=None, kept: bool | None=None, cursor: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 275) — ``pad.list``: pads most recently changed first, a page at a time, each with its first line.
- `key_between(a: str | None, b: str | None) -> str` ([source](../../../../../../src/learnloop/pads/blocks.py), line 322) — A position key strictly between ``a`` and ``b`` (either may be None: before or after everything).
- `apply_pad_ops(repository: Any, *, client_id: str, seq: int, pad_id: str, ops: list[Any], clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 545) — ``pad.apply``: one batch on one pad, applied once and in order (``learnloop.desks.protocol``).

### Module constants

- `EDITABLE_KINDS` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 35)
- `PAGE_SIZE` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 37)
- `PAD_OPS` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 170)
- `_DIGITS` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 301)

### Explicit exports

`__all__` declares:

- `EDITABLE_KINDS`
- `PAD_OPS`
- `PAGE_SIZE`
- `PadNotFound`
- `PadOp`
- `apply_pad_ops`
- `pad_list`
- `pad_view`

## Internal implementation anchors

- `class _Op(WireModel)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 40)
- `_block_out(head: dict[str, Any], created: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 179)
- `_pad_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 188)
- `class _Places` ([source](../../../../../../src/learnloop/pads/blocks.py), line 199) — Where a link points, enough to open it with no window of that source open (review finding 13): the source the reading belongs to (a ``ContentRef``'s ``source_id``), and on a transcript the cue's start (``t``, a video reference's time).
- `_inherited_anchors(connection: Any, heads: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 223) — Links a lifted block carries from the block it was lifted out of, where a lift made before links moved with the words left them on the stub: shown on the lifted block, read-only (``inherited_from_block_id`` names the stub's block, whose link events they are).
- `_midpoint(a: str, b: str | None) -> str` ([source](../../../../../../src/learnloop/pads/blocks.py), line 304)
- `_key_after(connection: Any, pad_id: str, head: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/pads/blocks.py), line 330) — A key right after ``head`` in its pad, before the next block; the head's own key when the next block shares it (equal keys order by block id: as close as the keys allow).
- `_keep_both(connection: Any, pad_id: str, client_id: str, op: EditBlock, head: dict[str, Any], base: dict[str, Any], now: str, heads: dict[str, str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 343) — A stale edit's words as a block of their own right after the current head; the head is left as it is.
- `_version_id(connection: Any, minted: str | None) -> str` ([source](../../../../../../src/learnloop/pads/blocks.py), line 370)
- `_current_head(connection: Any, pad_id: str, block_id: str, expected: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 378)
- `_successor(head: dict[str, Any], version_id: str, client_id: str, now: str, **changes: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 389)
- `_apply_pad_op(connection: Any, pad_id: str, client_id: str, op: Any, now: str, heads: dict[str, str], versions: dict[str, int]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/pads/blocks.py), line 397)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `PadNotFound`, `PadOp`, `apply_pad_ops`, `pad_list`, `pad_view`; statically calls `apply_pad_ops`, `pad_list`, `pad_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `reading_source`; calls `reading_source`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `anchor_event_exists`, `first_versions`, `head`, `heads`, `latest_anchor_event`, `lesson_additions_pads`, `list_pads`, `pad`, `standing_anchors_for_blocks`, `version`, `version_exists`
- [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] — imports `module`; calls `insert_anchor_event`, `insert_pad`, `insert_version`, `touch_pad`, `update_pad`
- [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] — imports `PAD`
- [[Reference/Modules/learnloop/desks/content_ref|learnloop.desks.content_ref]] — imports `WireModel`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `OpConflict`, `OpRefused`, `apply_batch`, `run_op`; calls `OpConflict`, `OpRefused`, `apply_batch`, `run_op`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `context_blocks`; calls `context_blocks`
- [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] — imports `module`; calls `copy_to_lifted`, `erase_in_batch`
- [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] — imports `tags`; calls `tags`

### Platform and third-party dependencies

- Standard library: `__future__`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/desk_helpers.py](../../../../../../tests/desk_helpers.py) — direct import
- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — direct import
  - `test_a_pads_links_name_their_source_and_time_so_a_closed_source_can_be_reopened`
  - `test_a_stale_edit_with_keep_both_keeps_the_server_head_and_lands_as_its_own_block`
  - `test_keep_both_on_a_current_head_is_an_ordinary_edit_and_a_removed_block_still_keeps_the_words`
  - `test_the_running_pad_is_ensured_once_with_its_stack_on_a_new_desk_and_an_old_one`
  - `test_the_server_places_a_block_between_two_keys_as_the_client_does`
  - `test_without_keep_both_a_stale_edit_remove_move_or_lift_is_a_conflict_naming_the_head_and_writes_nothing`
- [tests/test_reader_rd0_protocol.py](../../../../../../tests/test_reader_rd0_protocol.py) — direct import
  - `test_a_reused_client_id_is_a_refusal_and_the_outbox_moves_on`
  - `test_an_anchor_change_names_the_anchor_head_it_expects`
  - `test_an_anchor_op_without_its_expected_head_is_refused_by_the_params`
  - `test_blocks_chain_and_a_stale_edit_returns_the_current_head`
  - `test_pad_metadata_versions_and_keep`
  - `test_provenance_is_never_laundered`
  - `test_remove_move_lift_out_and_links`
  - `test_running_pads_show_on_their_desk_and_the_library_lists_pads`
- [tests/test_reader_rd4_emission.py](../../../../../../tests/test_reader_rd4_emission.py) — direct import
  - `test_a_lift_made_before_links_moved_still_carries_them`
  - `test_a_lift_out_takes_the_blocks_links_and_its_quotes_with_its_words`

## Modification guidance

- Make changes here when the responsibility remains blocks within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
