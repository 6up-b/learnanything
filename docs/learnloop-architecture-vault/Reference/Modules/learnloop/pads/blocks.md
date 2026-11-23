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
| Source lines | 349 |
| Owning package | [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CreatePad(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 39)
- `class SetTitle(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 48)
- `class Keep(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 54)
- `class Unkeep(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 59)
- `class InsertBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 64)
- `class EditBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 76)
- `class RemoveBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 85)
- `class MoveBlock(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 92)
- `class LiftOut(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 100)
- `class LinkAnchor(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 112)
- `class UnlinkAnchor(_Op)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 123)
- `class PadNotFound(LookupError)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 163)
- `pad_view(repository: Any, pad_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 167) — ``pad.get``: the pad, its standing blocks in order (removed blocks left out) and their links.
- `pad_list(repository: Any, *, desk_id: str | None=None, query: str | None=None, kept: bool | None=None, cursor: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 186) — ``pad.list``: pads most recently changed first, a page at a time, each with its first line.
- `apply_pad_ops(repository: Any, *, client_id: str, seq: int, pad_id: str, ops: list[Any], clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 328) — ``pad.apply``: one batch on one pad, applied once and in order (``learnloop.desks.protocol``).

### Module constants

- `EDITABLE_KINDS` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 30)
- `PAGE_SIZE` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 32)
- `PAD_OPS` ([src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py), line 138)

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

- `class _Op(WireModel)` ([source](../../../../../../src/learnloop/pads/blocks.py), line 35)
- `_block_out(head: dict[str, Any], created: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 147)
- `_pad_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 156)
- `_version_id(connection: Any, minted: str | None) -> str` ([source](../../../../../../src/learnloop/pads/blocks.py), line 211)
- `_current_head(connection: Any, pad_id: str, block_id: str, expected: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 219)
- `_successor(head: dict[str, Any], version_id: str, client_id: str, now: str, **changes: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/pads/blocks.py), line 230)
- `_apply_pad_op(connection: Any, pad_id: str, client_id: str, op: Any, now: str, heads: dict[str, str], versions: dict[str, int]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/pads/blocks.py), line 238)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]] — imports `PadNotFound`, `PadOp`, `apply_pad_ops`, `pad_list`, `pad_view`; statically calls `apply_pad_ops`, `pad_list`, `pad_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] — imports `module`; calls `first_versions`, `head`, `heads`, `insert_anchor_event`, `insert_pad`, `insert_version`, `list_pads`, `pad`, `standing_anchors_for_blocks`, `touch_pad`, `update_pad`, `version_exists`
- [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] — imports `PAD`
- [[Reference/Modules/learnloop/desks/content_ref|learnloop.desks.content_ref]] — imports `WireModel`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `OpConflict`, `OpRefused`, `apply_batch`, `run_op`; calls `OpConflict`, `OpRefused`, `apply_batch`, `run_op`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/pads|learnloop_sidecar.handlers.pads]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/desk_helpers.py](../../../../../../tests/desk_helpers.py) — direct import
- [tests/test_reader_rd0_protocol.py](../../../../../../tests/test_reader_rd0_protocol.py) — direct import
  - `test_blocks_chain_and_a_stale_edit_returns_the_current_head`
  - `test_pad_metadata_versions_and_keep`
  - `test_provenance_is_never_laundered`
  - `test_remove_move_lift_out_and_links`
  - `test_running_pads_show_on_their_desk_and_the_library_lists_pads`

## Modification guidance

- Make changes here when the responsibility remains blocks within learnloop.pads; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/pads/blocks.py](../../../../../../src/learnloop/pads/blocks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
