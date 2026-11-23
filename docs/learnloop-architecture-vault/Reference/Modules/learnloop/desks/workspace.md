---
title: "learnloop.desks.workspace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/desks/workspace.py"
source_paths:
  - "src/learnloop/desks/workspace.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.desks"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.desks.workspace module"
  - "src/learnloop/desks/workspace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-desks"
---

# `learnloop.desks.workspace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.desks.workspace` exists within [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] to own the behavior summarized by its module contract: Desks and their windows (spec §5.1, §5.2, §3.4): the state read and the ``desk.apply`` ops.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/desks/workspace.py](../../../../../../src/learnloop/desks/workspace.py) |
| Source lines | 573 |
| Owning package | [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CreateDesk(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 32)
- `class RenameDesk(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 41)
- `class ArchiveDesk(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 47)
- `class MoveDesk(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 52)
- `class OpenWindow(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 58)
  - `_content_or_stack(self) -> OpenWindow` (line 68; internal)
- `class CloseWindow(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 76)
- `class ReopenWindow(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 82)
- `class MoveWindow(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 89)
- `class MoveToDesk(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 96)
- `class Pair(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 106)
- `class Unpair(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 112)
- `class SetFocus(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 118)
- `class SetActivePane(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 124)
- `class SetView(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 130)
- `class SetDock(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 137)
- `class SetCompanionShown(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 143)
- `class SetGoal(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 149)
- `class AddToStack(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 155) — Put a pad (or a lesson) in a stack window: a union, so it commutes with every other change to the desk and needs no expected version (one given is not checked).
- `class RemoveFromStack(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 165) — Take a pad (or a lesson) out of a stack window, by the same rule; not there: nothing changes.
- `class EnsureRunningPad(_Op)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 174) — The desk's running pad (spec §10.5), created when it has none, and in a stack window of the desk, opened when it has none: idempotent, so every desk, new or old, gets one in one place.
- `desk_state(repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 221) — Every open desk with its slots, the running pads, and each client's last applied batch.
- `apply_desk_ops(repository: Any, *, client_id: str, seq: int, ops: list[Any], clock: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 558) — ``desk.apply``: one batch, applied once and in order (``learnloop.desks.protocol``).

### Module constants

- `PAIR_SIZE` ([src/learnloop/desks/workspace.py](../../../../../../src/learnloop/desks/workspace.py), line 24)
- `DOCKS` ([src/learnloop/desks/workspace.py](../../../../../../src/learnloop/desks/workspace.py), line 25)
- `DESK_OPS` ([src/learnloop/desks/workspace.py](../../../../../../src/learnloop/desks/workspace.py), line 193)

### Explicit exports

`__all__` declares:

- `DESK_OPS`
- `DOCKS`
- `DeskOp`
- `PAIR_SIZE`
- `apply_desk_ops`
- `desk_state`

## Internal implementation anchors

- `class _Op(WireModel)` ([source](../../../../../../src/learnloop/desks/workspace.py), line 28)
- `_window_out(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 203)
- `_slots(rows: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 214)
- `class _Layout` ([source](../../../../../../src/learnloop/desks/workspace.py), line 243) — One desk's open windows as a list of slots (each a list of window ids, panes in order).
- `_desk(connection: Any, desk_id: str, expected: int | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 283)
- `_window_desk(connection: Any, desk_id: str, window_id: str, expected: int | None, *, open_only: bool=True) -> tuple[dict, dict]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 294) — The window and the desk the op names, its version checked.
- `_apply_desk_op(connection: Any, op: Any, now: str, versions: dict[str, int]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/desks/workspace.py), line 312)
- `_open_desk(connection: Any, desk_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 468)
- `_same_entry(a: dict[str, Any], b: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/desks/workspace.py), line 477)
- `_stack_of(window: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 482)
- `_write_stack(connection: Any, window_id: str, stack: list[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/desks/workspace.py), line 486)
- `_stack_membership(connection: Any, op: AddToStack | RemoveFromStack, now: str, bump: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 490) — A stack's membership changed by one entry, whatever else changed on the desk meanwhile: the stack lives in the window's spec, apart from its view, so a whole-view write never drops a tab, and a union or a removal of one entry is the same at any desk version.
- `_ensure_running_pad(connection: Any, op: EnsureRunningPad, now: str, bump: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/desks/workspace.py), line 521) — The desk's running pad, and a stack window of the desk holding it: whichever is missing is created.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]] — imports `DeskOp`, `apply_desk_ops`, `desk_state`; statically calls `apply_desk_ops`, `desk_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/desks|learnloop.db.stores.desks]] — imports `module`; calls `desk`, `insert_desk`, `insert_window`, `open_desks`, `open_windows`, `update_desk`, `update_window`, `window`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `pad`, `running_pad_ids`
- [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] — imports `module`; calls `insert_pad`
- [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] — imports `DESK`
- [[Reference/Modules/learnloop/desks/content_ref|learnloop.desks.content_ref]] — imports `ContentRef`, `StackEntry`, `WireModel`
- [[Reference/Modules/learnloop/desks/protocol|learnloop.desks.protocol]] — imports `OpConflict`, `OpRefused`, `apply_batch`, `client_seq_heads`, `run_op`; calls `OpConflict`, `OpRefused`, `apply_batch`, `client_seq_heads`, `run_op`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/desks|learnloop_sidecar.handlers.desks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/desk_helpers.py](../../../../../../tests/desk_helpers.py) — direct import
- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — direct import
  - `test_a_pads_links_name_their_source_and_time_so_a_closed_source_can_be_reopened`
  - `test_the_running_pad_is_ensured_once_with_its_stack_on_a_new_desk_and_an_old_one`
- [tests/test_reader_rd0_protocol.py](../../../../../../tests/test_reader_rd0_protocol.py) — direct import
  - `test_a_batch_number_used_with_other_ops_is_refused`
  - `test_a_desk_carries_its_view_dock_shown_goal_and_order_and_archives`
  - `test_a_pad_stack_window_holds_pads_and_lessons`
  - `test_a_stale_head_is_a_conflict_with_the_current_head_and_is_not_applied`
  - `test_batches_replayed_out_of_order_converge_to_the_in_order_state`
  - `test_close_and_reopen_move_and_move_to_another_desk`
  - `test_desk_and_pad_batches_share_one_sequence_per_client`
  - `test_running_pads_show_on_their_desk_and_the_library_lists_pads`
  - `test_windows_open_beside_pair_at_most_two_and_unpair`
- [tests/test_reader_rd1_model_parity.py](../../../../../../tests/test_reader_rd1_model_parity.py) — direct import
  - `test_the_sidecar_gives_the_scripts_results_and_final_state`

## Modification guidance

- Make changes here when the responsibility remains workspace within learnloop.desks; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/desks/workspace.py](../../../../../../src/learnloop/desks/workspace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
